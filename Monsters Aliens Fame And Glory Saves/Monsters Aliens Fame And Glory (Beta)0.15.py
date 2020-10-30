import random
import time

"""Text wrapping and filling.
"""

# Copyright (C) 1999-2001 Gregory P. Ward.
# Copyright (C) 2002, 2003 Python Software Foundation.
# Written by Greg Ward <gward@python.net>

import re

__all__ = ['TextWrapper', 'wrap', 'fill', 'dedent', 'indent', 'shorten']

# Hardcode the recognized whitespace characters to the US-ASCII
# whitespace characters.  The main reason for doing this is that
# some Unicode spaces (like \u00a0) are non-breaking whitespaces.
_whitespace = '\t\n\x0b\x0c\r '

class TextWrapper:
    """
    Object for wrapping/filling text.  The public interface consists of
    the wrap() and fill() methods; the other methods are just there for
    subclasses to override in order to tweak the default behaviour.
    If you want to completely replace the main wrapping algorithm,
    you'll probably have to override _wrap_chunks().

    Several instance attributes control various aspects of wrapping:
      width (default: 70)
        the maximum width of wrapped lines (unless break_long_words
        is false)
      initial_indent (default: "")
        string that will be prepended to the first line of wrapped
        output.  Counts towards the line's width.
      subsequent_indent (default: "")
        string that will be prepended to all lines save the first
        of wrapped output; also counts towards each line's width.
      expand_tabs (default: true)
        Expand tabs in input text to spaces before further processing.
        Each tab will become 0 .. 'tabsize' spaces, depending on its position
        in its line.  If false, each tab is treated as a single character.
      tabsize (default: 8)
        Expand tabs in input text to 0 .. 'tabsize' spaces, unless
        'expand_tabs' is false.
      replace_whitespace (default: true)
        Replace all whitespace characters in the input text by spaces
        after tab expansion.  Note that if expand_tabs is false and
        replace_whitespace is true, every tab will be converted to a
        single space!
      fix_sentence_endings (default: false)
        Ensure that sentence-ending punctuation is always followed
        by two spaces.  Off by default because the algorithm is
        (unavoidably) imperfect.
      break_long_words (default: true)
        Break words longer than 'width'.  If false, those words will not
        be broken, and some lines might be longer than 'width'.
      break_on_hyphens (default: true)
        Allow breaking hyphenated words. If true, wrapping will occur
        preferably on whitespaces and right after hyphens part of
        compound words.
      drop_whitespace (default: true)
        Drop leading and trailing whitespace from lines.
      max_lines (default: None)
        Truncate wrapped lines.
      placeholder (default: ' [...]')
        Append to the last line of truncated text.
    """

    unicode_whitespace_trans = {}
    uspace = ord(' ')
    for x in _whitespace:
        unicode_whitespace_trans[ord(x)] = uspace

    # This funky little regex is just the trick for splitting
    # text up into word-wrappable chunks.  E.g.
    #   "Hello there -- you goof-ball, use the -b option!"
    # splits into
    #   Hello/ /there/ /--/ /you/ /goof-/ball,/ /use/ /the/ /-b/ /option!
    # (after stripping out empty strings).
    word_punct = r'[\w!"\'&.,?]'
    letter = r'[^\d\W]'
    whitespace = r'[%s]' % re.escape(_whitespace)
    nowhitespace = '[^' + whitespace[1:]
    wordsep_re = re.compile(r'''
        ( # any whitespace
          %(ws)s+
        | # em-dash between words
          (?<=%(wp)s) -{2,} (?=\w)
        | # word, possibly hyphenated
          %(nws)s+? (?:
            # hyphenated word
              -(?: (?<=%(lt)s{2}-) | (?<=%(lt)s-%(lt)s-))
              (?= %(lt)s -? %(lt)s)
            | # end of word
              (?=%(ws)s|\Z)
            | # em-dash
              (?<=%(wp)s) (?=-{2,}\w)
            )
        )''' % {'wp': word_punct, 'lt': letter,
                'ws': whitespace, 'nws': nowhitespace},
        re.VERBOSE)
    del word_punct, letter, nowhitespace

    # This less funky little regex just split on recognized spaces. E.g.
    #   "Hello there -- you goof-ball, use the -b option!"
    # splits into
    #   Hello/ /there/ /--/ /you/ /goof-ball,/ /use/ /the/ /-b/ /option!/
    wordsep_simple_re = re.compile(r'(%s+)' % whitespace)
    del whitespace

    # XXX this is not locale- or charset-aware -- string.lowercase
    # is US-ASCII only (and therefore English-only)
    sentence_end_re = re.compile(r'[a-z]'             # lowercase letter
                                 r'[\.\!\?]'          # sentence-ending punct.
                                 r'[\"\']?'           # optional end-of-quote
                                 r'\Z')               # end of chunk

    def __init__(self,
                 width=70,
                 initial_indent="",
                 subsequent_indent="",
                 expand_tabs=True,
                 replace_whitespace=True,
                 fix_sentence_endings=False,
                 break_long_words=True,
                 drop_whitespace=True,
                 break_on_hyphens=True,
                 tabsize=8,
                 *,
                 max_lines=None,
                 placeholder=' [...]'):
        self.width = width
        self.initial_indent = initial_indent
        self.subsequent_indent = subsequent_indent
        self.expand_tabs = expand_tabs
        self.replace_whitespace = replace_whitespace
        self.fix_sentence_endings = fix_sentence_endings
        self.break_long_words = break_long_words
        self.drop_whitespace = drop_whitespace
        self.break_on_hyphens = break_on_hyphens
        self.tabsize = tabsize
        self.max_lines = max_lines
        self.placeholder = placeholder


    # -- Private methods -----------------------------------------------
    # (possibly useful for subclasses to override)

    def _munge_whitespace(self, text):
        """_munge_whitespace(text : string) -> string

        Munge whitespace in text: expand tabs and convert all other
        whitespace characters to spaces.  Eg. " foo\\tbar\\n\\nbaz"
        becomes " foo    bar  baz".
        """
        if self.expand_tabs:
            text = text.expandtabs(self.tabsize)
        if self.replace_whitespace:
            text = text.translate(self.unicode_whitespace_trans)
        return text


    def _split(self, text):
        """_split(text : string) -> [string]

        Split the text to wrap into indivisible chunks.  Chunks are
        not quite the same as words; see _wrap_chunks() for full
        details.  As an example, the text
          Look, goof-ball -- use the -b option!
        breaks into the following chunks:
          'Look,', ' ', 'goof-', 'ball', ' ', '--', ' ',
          'use', ' ', 'the', ' ', '-b', ' ', 'option!'
        if break_on_hyphens is True, or in:
          'Look,', ' ', 'goof-ball', ' ', '--', ' ',
          'use', ' ', 'the', ' ', '-b', ' ', option!'
        otherwise.
        """
        if self.break_on_hyphens is True:
            chunks = self.wordsep_re.split(text)
        else:
            chunks = self.wordsep_simple_re.split(text)
        chunks = [c for c in chunks if c]
        return chunks

    def _fix_sentence_endings(self, chunks):
        """_fix_sentence_endings(chunks : [string])

        Correct for sentence endings buried in 'chunks'.  Eg. when the
        original text contains "... foo.\\nBar ...", munge_whitespace()
        and split() will convert that to [..., "foo.", " ", "Bar", ...]
        which has one too few spaces; this method simply changes the one
        space to two.
        """
        i = 0
        patsearch = self.sentence_end_re.search
        while i < len(chunks)-1:
            if chunks[i+1] == " " and patsearch(chunks[i]):
                chunks[i+1] = "  "
                i += 2
            else:
                i += 1

    def _handle_long_word(self, reversed_chunks, cur_line, cur_len, width):
        """_handle_long_word(chunks : [string],
                             cur_line : [string],
                             cur_len : int, width : int)

        Handle a chunk of text (most likely a word, not whitespace) that
        is too long to fit in any line.
        """
        # Figure out when indent is larger than the specified width, and make
        # sure at least one character is stripped off on every pass
        if width < 1:
            space_left = 1
        else:
            space_left = width - cur_len

        # If we're allowed to break long words, then do so: put as much
        # of the next chunk onto the current line as will fit.
        if self.break_long_words:
            cur_line.append(reversed_chunks[-1][:space_left])
            reversed_chunks[-1] = reversed_chunks[-1][space_left:]

        # Otherwise, we have to preserve the long word intact.  Only add
        # it to the current line if there's nothing already there --
        # that minimizes how much we violate the width constraint.
        elif not cur_line:
            cur_line.append(reversed_chunks.pop())

        # If we're not allowed to break long words, and there's already
        # text on the current line, do nothing.  Next time through the
        # main loop of _wrap_chunks(), we'll wind up here again, but
        # cur_len will be zero, so the next line will be entirely
        # devoted to the long word that we can't handle right now.

    def _wrap_chunks(self, chunks):
        """_wrap_chunks(chunks : [string]) -> [string]

        Wrap a sequence of text chunks and return a list of lines of
        length 'self.width' or less.  (If 'break_long_words' is false,
        some lines may be longer than this.)  Chunks correspond roughly
        to words and the whitespace between them: each chunk is
        indivisible (modulo 'break_long_words'), but a line break can
        come between any two chunks.  Chunks should not have internal
        whitespace; ie. a chunk is either all whitespace or a "word".
        Whitespace chunks will be removed from the beginning and end of
        lines, but apart from that whitespace is preserved.
        """
        lines = []
        if self.width <= 0:
            raise ValueError("invalid width %r (must be > 0)" % self.width)
        if self.max_lines is not None:
            if self.max_lines > 1:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent
            if len(indent) + len(self.placeholder.lstrip()) > self.width:
                raise ValueError("placeholder too large for max width")

        # Arrange in reverse order so items can be efficiently popped
        # from a stack of chucks.
        chunks.reverse()

        while chunks:

            # Start the list of chunks that will make up the current line.
            # cur_len is just the length of all the chunks in cur_line.
            cur_line = []
            cur_len = 0

            # Figure out which static string will prefix this line.
            if lines:
                indent = self.subsequent_indent
            else:
                indent = self.initial_indent

            # Maximum width for this line.
            width = self.width - len(indent)

            # First chunk on line is whitespace -- drop it, unless this
            # is the very beginning of the text (ie. no lines started yet).
            if self.drop_whitespace and chunks[-1].strip() == '' and lines:
                del chunks[-1]

            while chunks:
                l = len(chunks[-1])

                # Can at least squeeze this chunk onto the current line.
                if cur_len + l <= width:
                    cur_line.append(chunks.pop())
                    cur_len += l

                # Nope, this line is full.
                else:
                    break

            # The current line is full, and the next chunk is too big to
            # fit on *any* line (not just this one).
            if chunks and len(chunks[-1]) > width:
                self._handle_long_word(chunks, cur_line, cur_len, width)
                cur_len = sum(map(len, cur_line))

            # If the last chunk on this line is all whitespace, drop it.
            if self.drop_whitespace and cur_line and cur_line[-1].strip() == '':
                cur_len -= len(cur_line[-1])
                del cur_line[-1]

            if cur_line:
                if (self.max_lines is None or
                    len(lines) + 1 < self.max_lines or
                    (not chunks or
                     self.drop_whitespace and
                     len(chunks) == 1 and
                     not chunks[0].strip()) and cur_len <= width):
                    # Convert current line back to a string and store it in
                    # list of all lines (return value).
                    lines.append(indent + ''.join(cur_line))
                else:
                    while cur_line:
                        if (cur_line[-1].strip() and
                            cur_len + len(self.placeholder) <= width):
                            cur_line.append(self.placeholder)
                            lines.append(indent + ''.join(cur_line))
                            break
                        cur_len -= len(cur_line[-1])
                        del cur_line[-1]
                    else:
                        if lines:
                            prev_line = lines[-1].rstrip()
                            if (len(prev_line) + len(self.placeholder) <=
                                    self.width):
                                lines[-1] = prev_line + self.placeholder
                                break
                        lines.append(indent + self.placeholder.lstrip())
                    break

        return lines

    def _split_chunks(self, text):
        text = self._munge_whitespace(text)
        return self._split(text)

    # -- Public interface ----------------------------------------------

    def wrap(self, text):
        """wrap(text : string) -> [string]

        Reformat the single paragraph in 'text' so it fits in lines of
        no more than 'self.width' columns, and return a list of wrapped
        lines.  Tabs in 'text' are expanded with string.expandtabs(),
        and all other whitespace characters (including newline) are
        converted to space.
        """
        chunks = self._split_chunks(text)
        if self.fix_sentence_endings:
            self._fix_sentence_endings(chunks)
        return self._wrap_chunks(chunks)

    def fill(self, text):
        """fill(text : string) -> string

        Reformat the single paragraph in 'text' to fit in lines of no
        more than 'self.width' columns, and return a new string
        containing the entire wrapped paragraph.
        """
        return "\n".join(self.wrap(text))


# -- Convenience interface ---------------------------------------------

def wrap(text, width=70, **kwargs):
    """Wrap a single paragraph of text, returning a list of wrapped lines.

    Reformat the single paragraph in 'text' so it fits in lines of no
    more than 'width' columns, and return a list of wrapped lines.  By
    default, tabs in 'text' are expanded with string.expandtabs(), and
    all other whitespace characters (including newline) are converted to
    space.  See TextWrapper class for available keyword args to customize
    wrapping behaviour.
    """
    w = TextWrapper(width=width, **kwargs)
    return w.wrap(text)

def fill(text, width=70, **kwargs):
    """Fill a single paragraph of text, returning a new string.

    Reformat the single paragraph in 'text' to fit in lines of no more
    than 'width' columns, and return a new string containing the entire
    wrapped paragraph.  As with wrap(), tabs are expanded and other
    whitespace characters converted to space.  See TextWrapper class for
    available keyword args to customize wrapping behaviour.
    """
    w = TextWrapper(width=width, **kwargs)
    return w.fill(text)

def shorten(text, width, **kwargs):
    """Collapse and truncate the given text to fit in the given width.

    The text first has its whitespace collapsed.  If it then fits in
    the *width*, it is returned as is.  Otherwise, as many words
    as possible are joined and then the placeholder is appended::

        >>> textwrap.shorten("Hello  world!", width=12)
        'Hello world!'
        >>> textwrap.shorten("Hello  world!", width=11)
        'Hello [...]'
    """
    w = TextWrapper(width=width, max_lines=1, **kwargs)
    return w.fill(' '.join(text.strip().split()))


# -- Loosely related functionality -------------------------------------

_whitespace_only_re = re.compile('^[ \t]+$', re.MULTILINE)
_leading_whitespace_re = re.compile('(^[ \t]*)(?:[^ \t\n])', re.MULTILINE)

def dedent(text):
    """Remove any common leading whitespace from every line in `text`.

    This can be used to make triple-quoted strings line up with the left
    edge of the display, while still presenting them in the source code
    in indented form.

    Note that tabs and spaces are both treated as whitespace, but they
    are not equal: the lines "  hello" and "\\thello" are
    considered to have no common leading whitespace.

    Entirely blank lines are normalized to a newline character.
    """
    # Look for the longest leading string of spaces and tabs common to
    # all lines.
    margin = None
    text = _whitespace_only_re.sub('', text)
    indents = _leading_whitespace_re.findall(text)
    for indent in indents:
        if margin is None:
            margin = indent

        # Current line more deeply indented than previous winner:
        # no change (previous winner is still on top).
        elif indent.startswith(margin):
            pass

        # Current line consistent with and no deeper than previous winner:
        # it's the new winner.
        elif margin.startswith(indent):
            margin = indent

        # Find the largest common whitespace between current line and previous
        # winner.
        else:
            for i, (x, y) in enumerate(zip(margin, indent)):
                if x != y:
                    margin = margin[:i]
                    break

    # sanity check (testing/debugging only)
    if 0 and margin:
        for line in text.split("\n"):
            assert not line or line.startswith(margin), \
                   "line = %r, margin = %r" % (line, margin)

    if margin:
        text = re.sub(r'(?m)^' + margin, '', text)
    return text


def indent(text, predicate=None):
    """Adds 'prefix' to the beginning of selected lines in 'text'.

    If 'predicate' is provided, 'prefix' will only be added to the lines
    where 'predicate(line)' is True. If 'predicate' is not provided,
    it will default to adding 'prefix' to all non-empty lines that do not
    consist solely of whitespace characters.
    """
    if predicate is None:
        def predicate(line):
            return line.strip()

    def prefixed_lines():
        for line in text.splitlines(True):
            yield ("  " + line if predicate(line) else line)
    return ''.join(prefixed_lines())

'''
if __name__ == "__main__":
    #print dedent("\tfoo\n\tbar")
    #print dedent("  \thello there\n  \t  how are you?")
    print(dedent("Hello there.\n  This is indented."))
'''

actiontype = set([])
action2 = ""
printd = 0
description = 1
generalpart = "base_universe"
part = "grassy_field"
previouspart = []
previouspart.append(part)
done = 0
dialogcharacter = ""
dialogpart = ""
dialogspecificpart = 0
indialog = 0
choosedialog = 0
dialogschosen = []
yesornotype = ""
yesornoaction = 0
isfloornumberaction = 0
isjustfloornumberaction = 0
placesdiscovered = set([])
placesdiscovered.add(part)
printplacesdiscovered = ["Grassy Field"]
inventory = {"cabin_key":1, "cabin_upstairs_bedroom_key":0, "water_bucket":1, "bucket":0, "unlit_torch":0, "lit_torch":0, "ladder":0, "portal_gun":1}
questlist = {"get_rick_duff_beer": 1, "get_bart_slingshot": 0, "get_bart_skateboard": 0}
lockeddoors = {"cabin_front_door":1, "cabin_attic_hatch":1}
changableobjects = {"lit_cabin_fireplace":1, "cabin_upstairs_bedroom_key_on_table":1, "ladder_on_side_of_cabin":1, "cabin_attic_ladder_placed":1}
beento = {"grassy_field":0, "cavepart1":0}
enemiesalive = {"cavepart2_r1_imp": 1}
npcstats = {"health_cavepart2_r1_imp": 10, "attack_cavepart2_r1_imp": 2, "defence_cavepart2_r1_imp": 1}
paratype = 1
developermode = 0
healthpoints = 20
attackpoints = 0
defencepoints = 0

cabindict = set(["cabin", "log cabin", "creepy log cabin"])
bathroomdict = set(["bathroom", "bath room", "washroom", "wash room"])
bedroomdict = set(["bedroom", "bed room"])
livingroomdict = set(["living room", "livingroom", "main room", "lobby"])
grassyfielddict = set(["grassy field", "field", "open field"])
mineshaftdict = set(["mineshaft", "mine shaft", "mine", "cave", "mine cave"])
forestdict = set(["forest", "woods", "tree forest"])

neswdict = set(["n", "north", "e", "east", "s", "south", "w", "west", "ne", "n e", "n-e", "northeast", "north east", "north-east", "se", "s e", "s-e", "southeast", "south east", "south-east", "sw", "s w", "s-w", "southwest", "south west", "south-west", "nw", "n w", "n-w", "northwest", "north west", "north-west"])

floor1dict = set(["1st floor", "1stfloor", "floor 1", "first floor"])
floor2dict = set(["2nd floor", "2ndfloor", "floor 2", "second floor"])
floor3dict = set(["3rd floor", "3rdfloor", "floor 3", "third floor"])
floornumberdict = set(["1st floor", "1stfloor", "floor 1", "first floor", "2nd floor", "2ndfloor", "floor 2", "second floor", "3rd floor", "3rdfloor", "floor 3", "third floor"])

'''
gotoupstairsdict = set(["upstairs", "upper floor", "next floor up"])
gotodownstairsdict = set(["downstairs", "lower floor", "next floor down"])
'''

gotoupstairsdict = set(["upstairs", "up stairs", "upper floor", "up a level", "up", "u", "next floor up"])
gotodownstairsdict = set(["downstairs", "down stairs", "lower floor", "down a level", "down", "d", "next floor down"])

opepcurtainsdict = set(["pull back curtain", "pull back curtains", "open curtain", "open curtains", "draw back curtain", "draw back curtains"])
lighttorchonfiredict = set(["light torch on fire", "light torch ablaze", "light torch"])
fireplacedict = set(["fireplace", "fire place"])
takeobjectdict = set(["take", "grab", "snatch", "pick up"])

spaceafteractiondict = set([" ", ""])

abilities = set(["pick up"])

random_require_string = ""
random_need_to_string = ""

def randomtext():
    global random_require_string
    global random_need_to_string
    global random_unlock_string
    global random_seems_to_be_string
    global random_there_is_string
    
    random_num = random.randint(1,2)
    if random_num == 1:
        random_require_string = "require"
    elif random_num == 2:
        random_require_string = "need"
        
    random_num = random.randint(1,2)
    if random_num == 1:
        random_need_to_string = "need"
    elif random_num == 2:
        random_need_to_string = "have"
        
    random_num = random.randint(1,3)
    if random_num == 1:
        random_unlock_string = "unlock"
    elif random_num == 2:
        random_unlock_string = "get into"
    elif random_num == 3:
        random_unlock_string = "open"
    
    random_num = random.randint(1,3)
    if random_num == 1:
        random_seems_to_be_string = "seems"
    elif random_num == 2:
        random_seems_to_be_string = "appears"
    elif random_num == 3:
        random_seems_to_be_string = "looks"
        
    random_num = random.randint(1,3)
    if random_num == 1:
        stage2_random_seems_to_be_string = "seems"
    elif random_num == 2:
        stage2_random_seems_to_be_string = "appears"
    elif random_num == 3:
        stage2_random_seems_to_be_string = "looks"
    while random_seems_to_be_string == stage2_random_seems_to_be_string:
        random_num = random.randint(1,3)
        if random_num == 1:
            stage2_random_seems_to_be_string = "seems"
        elif random_num == 2:
            stage2_random_seems_to_be_string = "appears"
        elif random_num == 3:
            stage2_random_seems_to_be_string = "looks"
        
    random_num = random.randint(1,5)
    if random_num == 1:
        random_there_is_string = "There is"
    elif random_num == 2:
        random_there_is_string = "You notice there is"
    elif random_num > 2:
        random_there_is_string = str("There " + stage2_random_seems_to_be_string + " to be")

def calculateactiontype():
    #Makes all the variables in the function global
    global action
    global action2
    global actiontype
    global part
    global description
    global done
    global yesornoaction
    action = action.strip()
    
    if action == "print d" or action == "print description":
        actiontype = set(["printd"])
        return
        
    if action == "settings" or action == "list settings":
        actiontype = set(["settings"])
        return
        
    savegamedict = set(["save", "save game"])
    if action in savegamedict:
        actiontype = set(["save"])
        return
    
    '''
    goupstairsdict = set(["go upstairs", "go up stairs", "go up a level", "go up", "go u", "u"])
    if action in goupstairsdict:
        actiontype = set(["go upstairs"])
        return
    
    godownstairsdict = set(["go downstairs", "go down stairs", "go down a level", "go down", "go d", "d"])
    if action in godownstairsdict:
        actiontype = set(["go downstairs"])
        return
    '''
    
    if action in neswdict:
        actiontype = set(["move"])
        return
    
    leftdict = set(["left", "l"])
    if action in leftdict:
        actiontype = set(["left"])
        return
        
    rightdict = set(["right", "r"])
    if action in rightdict:
        actiontype = set(["right"])
        return
    
    gobackdict = set(["go back", "go to previous part"])
    if action in gobackdict:
        actiontype = set(["go back"])
        return
    
    
    loadgamedict = set(["load game", "load"])
    examinedict = set(["examine", "x", "inspect", "describe", "check"])
    tptodict = set(["tp to", "tp"])
    enterdict = set(["enter", "go inside", "go in"])
    leavedict = set(["leave", "exit"])
    gotodict = set(["go to", "go"])
    fightdict = set(["beat up", "fight", "pick a fight with", "battle"])
    
    printdict = set(["print", "list", "show", "open"])
    
    amountofactions = 0
    action2 = action
    for item in set(list(loadgamedict) + list(examinedict) + list(tptodict) + list(enterdict) + list(leavedict) + list(gotodict) + list(takeobjectdict) + list(fightdict)):
        index = action2.find(item)
        if item in action2 and action2[index + len(item):index + len(item) + 1] in spaceafteractiondict:
            action2 = action2[:index] + action2[index + len(item) + 1:]
            amountofactions = amountofactions + 1
    if amountofactions > 1:
        print("You typed to many actions.")
        done = 1
        return
    
    for item in set(list(loadgamedict) + list(examinedict) + list(tptodict) + list(enterdict) + list(leavedict) + list(gotodict) + list(takeobjectdict) + list(fightdict)):
        if action.find(item) == 0 and action[len(item):len(item) + 1] in spaceafteractiondict:
            if item == "go" and (action.find("go inside") == 0 or action.find("go in") == 0 or action.find("go to") == 0):
                action = action
            else:
                action = action[len(item) + 1:]
                action = action.strip()
              
            if action == "" and item not in set(list(leavedict) + list(enterdict)):
                if item in loadgamedict:
                    print("Enter save game data to load save:")
                elif item in examinedict:
                    print("What do you want to examine?")
                elif item in tptodict:
                    print("Where do you want to teleport to?")
                elif item in gotodict:
                    print("Where would you like to " + item + "?")
                elif item in set(list(takeobjectdict) + list(fightdict)):
                    print("What do you want to " + item + "?")
                action = input(">").lower()
                action = action.strip()
            elif action == "" and item in enterdict and part != "cabin_front" and part != "simpsons_house_front":
                print("What would you like to " + item + "?")
                action = input(">").lower()
                action = action.strip()
            if item in loadgamedict:
                actiontype = set(["load", "save"])
            elif item in examinedict:
                actiontype = set(["examine"])
            elif item in tptodict:
                actiontype = set(["teleport"])
            elif item in enterdict:
                actiontype = set(["enter"])
            elif item in leavedict:
                actiontype = set(["leave"])
            elif item in gotodict:
                if action in neswdict:
                    actiontype = set(["move"])
                elif action in leftdict:
                    actiontype = set(["left"])
                elif action in rightdict:
                    actiontype = set(["right"])
                else:
                    actiontype = set(["go to"])
            elif item in fightdict:
                actiontype = set(["fight"])
                action2 = item
            elif item in takeobjectdict:
                actiontype = set(["take"])
                action2 = item
                
class descriptionstuff():
    global printdescriptionaction
    global printdescription
    
    def printdescriptionaction():
        #Makes all the variables in the function global
        global action
        global part
        global description
        global done
        global yesornoaction
        global printd
        if action == "print d":
            printd = 1
            description = 1
            done = 1
    
    #Function to print a description of your surroundings when you enter a new location
    def printdescription():
        #Makes all the variables in the function global
        global action
        global part
        global description
        global done
        global yesornoaction
        
        global random_require_string
        global random_need_to_string
        global random_unlock_string
        global random_seems_to_be_string
        global random_there_is_string
        
        #Provides a description of your surroundings when you move into a new place
        if description > 0:
            if part == "grassy_field":
                print('GRASSY FIELD')
            elif part == "mineshaft_entrance":
                print('MINESHAFT ENTRANCE')
            elif part == "cavepart1" or part == "cavepart2":
                print('CAVE')
            elif part == "forestpart1" or part == "forestpart2":
                print('FOREST')
            elif part == "cabin_front" or part == "cabin_living_room" or part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom" or part == "cabin_2nd_floor_bedroom_connecter" or part == "cabin_attic":
                print('CABIN')
            '''
            elif part == "cabin_living_room":
                print('CABIN')
                print('-LIVING ROOM')
            '''
            if paratype == 1:
                if description == 1:
                    '''
                    if part == "grassy_field" and beento["grassy_field"] == 0:
                        print('  You awaken in a grassy field surrounded by mountains. You have\nno idea who you are or how you got here.\n')
                        beento["grassy_field"] = 1
                        
                    if part == "grassy_field":
                        print('  There looks to be a mineshaft far off into the distance,\ntunneling into one of the mountains, to the west. There is also\na creepy old looking log cabin to the south east and a forest\nto the north.')
                    
                    if part == "forestpart1":
                        print('  You walk into a forest.')
                    
                    if part == "cabin_front":
                        print('  You stand at the front entrance of the creepy log cabin.')
                    
                    if part == "cabin_living_room":
                        print('  In the living room there is a table in the middle and a lit\nfireplace.')
                    
                    if part == "cabin_1st_floor_bathroom":
                        print('  You enter the bathroom.')
                        
                    if part == "cabin_2nd_floor_bedroom_connecter":
                        print('  You go upstairs and come to a hallway bedroom connecter. You\nnotice several closed doors, a bedroom door, a bathroom door,\nand a attic hatch on the ceiling.')
                        
                    if part == "mineshaft_entrance":
                        print('  You stand at the entrance to the mineshaft. All you can see is\ndarkness, and you smell the strong stench of sulfur emanating\nfrom the cave.')
                    
                    if part == "cavepart1" and beento["cavepart1"] == 0:
                        print('  You are now in the pitch black cave. You are surrounded by\ndarkness, but there is a faint light coming from down the\ntunnel. The smell of sulfur has gotten stronger although their\nis now a new stench, it smells of decaying meat. If you decide\nto go further into the tunnel like cave, go west.')
                        beento["cavepart1"] = 1
                        
                    elif part == "cavepart1":
                        print('  You are in the pitch black cave. You are surrounded by\ndarkness, but there is a faint light coming from down the\ntunnel. There is a strong smell of sulfur and decaying meat. If\nyou decide to go further into the tunnel like cave, go west.')
                    
                    if part == "cavepart2":
                        print('  As you continue further into the cave the potent smells\ncontinue to get stronger and stronger, however the light at the\nend of the tunnel proceeds to grow brighter. Eventually you\ncome to a branching split in the cave where there are two\ntunnels, one to the left and one to the right. As you decide\nwhich way to go you notice something you havent noticed before.\nBeing so caught up in thinking about where the tunnel leads,\nyou look around and notice that everything as become very block\nlike, almost as if your mind has lost the ability to perceive\nslopes, spheres or angles. You also notice where the light has\nbeen coming from this whole time as there is an also block like\ntorch pinned to the wall between the two branching paths.')
                    
                    if part == "cavepart2_l1":
                        print('  You decide to travel down the left tunnel which eventually\nstarts too open up into a large room filled with mine carts and\nbright block like torches. You also notice people but they\naren\'t normal people, NO! They are all blocky, their arms,\ntheir legs, even their heads!')
                        '''
                    if part == "grassy_field" and beento["grassy_field"] == 0:
                        print(fill(indent('You awaken in a grassy field surrounded by mountains. You have no idea who you are or how you got here.\n')))
                        beento["grassy_field"] = 1
                        
                    if part == "grassy_field":
                        print(fill(indent('There looks to be a mineshaft far off into the distance, tunneling into one of the mountains, to the west. There is also a creepy old looking log cabin to the south east and a forest to the north.')))
                    
                    if part == "forestpart1":
                        print(fill(indent('You walk into a forest.')))
                    
                    
                    if part == "cabin_front":
                        if changableobjects["ladder_on_side_of_cabin"] == 1 and lockeddoors["cabin_front_door"] == 1:
                            print(fill(indent('You stand at the front entrance of the creepy log cabin. ' + random_there_is_string + ' a ladder leaning against the side of the cabin and the front door ' + random_seems_to_be_string + ' to be locked.')))
                            
                        elif changableobjects["ladder_on_side_of_cabin"] == 1 and lockeddoors["cabin_front_door"] == 0:
                            print(fill(indent('You stand at the front entrance of the creepy log cabin. ' + random_there_is_string + ' a ladder leaning against the side of the cabin.')))
                        elif changableobjects["ladder_on_side_of_cabin"] == 0 and lockeddoors["cabin_front_door"] == 1:
                            print(fill(indent('You stand at the front entrance of the creepy log cabin. The front door ' + random_seems_to_be_string + ' to be locked.')))
                            
                        elif changableobjects["ladder_on_side_of_cabin"] == 0 and lockeddoors["cabin_front_door"] == 0:
                            print(fill(indent('You stand at the front entrance of the creepy log cabin.')))
                    
                    
                    if part == "cabin_living_room":
                        print(fill(indent('In the living room there is a table in the middle and a lit fireplace.')))
                    
                    if part == "cabin_1st_floor_bathroom":
                        print(fill(indent('You enter the bathroom.')))
                        
                    if part == "cabin_2nd_floor_bedroom_connecter" and (action in gotoupstairsdict or isfloornumberaction == 2):
                        print(fill(indent('You go upstairs and come to a hallway bedroom connecter. You notice several closed doors, a bedroom door, a bathroom door, and a attic hatch on the ceiling.')))
                    elif part == "cabin_2nd_floor_bedroom_connecter":
                        print(fill(indent('You come to a hallway bedroom connecter. You notice several closed doors, a bedroom door, a bathroom door, a attic hatch on the ceiling as well as stairs to the main floor.')))
                    
                    if part == "cabin_attic" and printd == 1:
                        print(fill(indent('You are in the attic.')))
                    elif part == "cabin_attic":
                        print(fill(indent('You arrive in the attic.')))
                        
                    if part == "mineshaft_entrance":
                        print(fill(indent('You stand at the entrance to the mineshaft. All you can see is darkness, and you smell the strong stench of sulfur emanating from the cave.')))
                    
                    if part == "cavepart1" and beento["cavepart1"] == 0:
                        print(fill(indent('You are now in the pitch black cave. You are surrounded by darkness, but there is a faint light coming from down the tunnel. The smell of sulfur has gotten stronger although their is now a new stench, it smells of decaying meat. If you decide to go further into the tunnel like cave, go west.')))
                        beento["cavepart1"] = 1
                    elif part == "cavepart1":
                        print(fill(indent('You are in the pitch black cave. You are surrounded by darkness, but there is a faint light coming from down the tunnel. There is a strong smell of sulfur and decaying meat. If you decide to go further into the tunnel like cave, go west.')))
                    
                    if part == "cavepart2" and beento["cavepart2"] == 0:
                        print(fill(indent('You stand at a branching split in the cave where there are two tunnels, one to the left and to the right. You also notice that everything is very block like. There are block like torches pinned to the walls.')))
                        beento["cavepart2"] = 1
                        
                        print(fill(indent('As you continue further into the cave the potent smells continue to get stronger and stronger, however the light at the end of the tunnel proceeds to grow brighter. Eventually you come to a branching split in the cave where there are two tunnels, one to the left and one to the right. As you decide which way to go you notice something you havent noticed before. Being so caught up in thinking about where the tunnel leads, you look around and notice that everything has become very block like, almost as if your mind has lost the ability to perceive slopes, spheres or angles. You also notice where the light has been coming from this whole time as there are block like torches pinned to the walls.')))
                    
                    if part == "cavepart2_l1":
                        print(fill(indent('You decide to travel down the left tunnel which eventually starts too open up into a large room filled with mine carts and bright block like torches. You also notice people but they aren\'t normal people, NO! They are all blocky, their arms, their legs, even their heads!')))
                        
                    if part == "cavepart2_r1":
                        print(fill(indent('There is an imp blocking the path.')))
            elif paratype == 2:
                if description == 1:
                    if part == "grassy_field" and beento["grassy_field"] == 0:
                        print('  You awaken in a grassy field surrounded by mountains. You have no idea who you are or how you got here.\n')
                        beento["grassy_field"] = 1
                        
                    if part == "grassy_field":
                        print('  There looks to be a mineshaft far off into the distance, tunneling into one of the mountains, to the west. There is also a creepy old looking log cabin to the south east and a forest to the north.')
                    
                    if part == "forestpart1":
                        print('  You walk into a forest.')
                    
                    if part == "cabin_front":
                        print('  You stand at the front entrance of the creepy log cabin.')
                    
                    if part == "cabin_living_room":
                        print('  In the living room there is a table in the middle and a lit fireplace.')
                    
                    if part == "cabin_1st_floor_bathroom":
                        print('  You enter the bathroom.')
                        
                    if part == "cabin_2nd_floor_bedroom_connecter":
                        print('  You go upstairs and come to a hallway bedroom connecter. You notice several closed doors, a bedroom door, a bathroom door, and a attic hatch on the ceiling.')
                        
                    if part == "mineshaft_entrance":
                        print('  You stand at the entrance to the mineshaft. All you can see is darkness, and you smell the strong stench of sulfur emanating from the cave.')
                    
                    if part == "cavepart1" and beento["cavepart1"] == 0:
                        print('  You are now in the pitch black cave. You are surrounded by darkness, but there is a faint light coming from down the tunnel. The smell of sulfur has gotten stronger although their is now a new stench, it smells of decaying meat. If you decide to go further into the tunnel like cave, go west.')
                        beento["cavepart1"] = 1
                        
                    elif part == "cavepart1":
                        print('  You are in the pitch black cave. You are surrounded by darkness, but there is a faint light coming from down the tunnel. There is a strong smell of sulfur and decaying meat. If you decide to go further into the tunnel like cave, go west.')
                    
                    if part == "cavepart2":
                        print('  As you continue further into the cave the potent smells continue to get stronger and stronger, however the light at the end of the tunnel proceeds to grow brighter. Eventually you come to a branching split in the cave where there are two tunnels, one to the left and one to the right. As you decide which way to go you notice something you havent noticed before. Being so caught up in thinking about where the tunnel leads, you look around and notice that everything as become very block like, almost as if your mind has lost the ability to perceive slopes, spheres or angles. You also notice where the light has been coming from this whole time as there is an also block like torch pinned to the wall between the two branching paths.')
                    
                    if part == "cavepart2_l1":
                        print('  You decide to travel down the left tunnel which eventually starts too open up into a large room filled with mine carts and bright block like torches. You also notice people but they aren\'t normal people, NO! They are all blocky, their arms, their legs, even their heads!')
                        
            description = 0
            done = 1

def settings():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    global paratype
    global developermode
    if action == "settings" or action == "list settings":
        print("Settings:")
        print(" - paratype = " + str(paratype) + " (default: 1) [1,2]")
        print(" - developer mode = " + str(developermode) + " (default: 0) [0,1]")
        done = 1
    elif action == "paratype = 1":
        paratype = 1
        print(" - paratype = " + str(paratype) + " (default: 1) [1,2]")
        done = 1
    elif action == "paratype = 2":
        paratype = 2
        print(" - paratype = " + str(paratype) + " (default: 1) [1,2]")
        done = 1
    elif action == "developer mode = 0":
        developermode = 0
        print(" - developer mode = " + str(developermode) + " (default: 0) [0,1]")
        done = 1
    elif action == "developer mode = 1":
        developermode = 1
        print(" - developer mode = " + str(developermode) + " (default: 0) [0,1]")
        done = 1


def save():
    #Makes all the variables in the function global
    global action
    global actiontype
    global part
    global description
    global done
    global yesornoaction
    global inventory
    global lockeddoors
    global changableobjects
    global beento
    global enemiesalive
    global paratype
    global developermode
    if "save" in actiontype:
        savesettings = " "
        savesettings = " " + str(paratype) + ":1 " + str(developermode) + ":2 "
        savepart = part
        saveplacesdiscovered = " "
        for item in placesdiscovered:
            saveplacesdiscovered = saveplacesdiscovered + item + " "
        saveinventory = " "
        for key in inventory:
            saveinventory = saveinventory + str(key) + ":" + str(inventory[key]) + " "
        savelockeddoors = " "
        for key in lockeddoors:
            savelockeddoors = savelockeddoors + str(key) + ":" + str(lockeddoors[key]) + " "
        savechangableobjects = " "
        for key in changableobjects:
            savechangableobjects = savechangableobjects + str(key) + ":" + str(changableobjects[key]) + " "
        savebeento = " "
        for key in beento:
            savebeento = savebeento + str(key) + ":" + str(beento[key]) + " "
        saveenemiesalive = " "
        for key in enemiesalive:
            saveenemiesalive = saveenemiesalive + str(key) + ":" + str(enemiesalive[key]) + " "
        savefile = {savesettings:0, savepart:1, saveplacesdiscovered:2, saveinventory:3, savelockeddoors:4, savechangableobjects:5, savebeento:6, saveenemiesalive:7}
        print("")
        print("Type:")
        print("")
        print("load " + str(savefile))
        print("")
        if "load" in actiontype:
            print("In order to load your game if save data is corupt.")
            actiontype.remove("save")
        else:
            print("In order to load your game.")
            done = 1
        print("You saved the game.")
            
def load():
    #Makes all the variables in the function global
    global action
    global actiontype
    global part
    global description
    global done
    global yesornoaction
    global inventory
    global lockeddoors
    global changableobjects
    global beento
    global paratype
    global developermode
    if "load" in actiontype:
        print("")
        if (action[:1] == "{") and (action[-1:] == "}"):
            # Check version for load command
            # if action2 == "version 0.15":
                # Load things
                
            #Loads settings
            index2 = action.find("': 0")
            action2 = action[3:index2]
            index = action2.find(":1 ")
            action2 = action2[:index]
            paratype = int(action2)
            
            index2 = action.find("': 0")
            action2 = action[3:index2]
            index2 = action2.find(":2 ")
            action2 = action2[index + 3:index2]
            developermode = int(action2)
            
            #Loads part
            index2 = action.find("': 0")
            index = action.find("': 1")
            part = action[index2 + 7:index]
            
            #Loads places discovered
            index2 = action.find("': 2")
            action2 = action[index + 8:index2]
            for index, word in enumerate(action2.split()):
                placesdiscovered.add(word)
            # print(placesdiscovered)
            
            #Loads inventory
            index = action.find("': 3")
            action2 = action[index2 + 8:index]
            inventory = {}
            for index, word in enumerate(action2.split()):
                index3 = word.find(":")
                inventory[word[:index3]] = int(word[index3 + 1:])
            # print(inventory)
            
            #Loads locked/unlocked doors
            index = action.find("': 3")
            index2 = action.find("': 4")
            action2 = action[index + 8:index2]
            lockeddoors = {}    
            for index, word in enumerate(action2.split()):
                index3 = word.find(":")
                lockeddoors[word[:index3]] = int(word[index3 + 1:])
            # print(lockeddoors)
            
            #Loads changable object states
            index = action.find("': 4")
            index2 = action.find("': 5")
            action2 = action[index + 8:index2]
            changableobjects = {}    
            for index, word in enumerate(action2.split()):
                index3 = word.find(":")
                changableobjects[word[:index3]] = int(word[index3 + 1:])
            # print(changableobjects)
            
            #Loads places visited
            index = action.find("': 5")
            index2 = action.find("': 6")
            action2 = action[index + 8:index2]
            beento = {}    
            for index, word in enumerate(action2.split()):
                index3 = word.find(":")
                beento[word[:index3]] = int(word[index3 + 1:])
            # print(beento)
            
            #Loads enemies alive
            index = action.find("': 6")
            index2 = action.find("': 7")
            action2 = action[index + 8:index2]
            enemiesalive = {}    
            for index, word in enumerate(action2.split()):
                index3 = word.find(":")
                enemiesalive[word[:index3]] = int(word[index3 + 1:])
            # print(enemiesalive)
            
            print(">You loaded the game from your savefile.")
            description = 1
            done = 1

#Function to check if the action is an examine command and then determines
#what to examine and then prints the description of the examined object or
#thing
def examine():
    #Makes all the variables in the function global
    global action
    global actiontype
    global part
    global description
    global done
    global yesornoaction
    global npcstats
    #Determines if the action is a examine command
    '''
    if ("examine" in action) or (action.find("x") == 0) or ("describe" in action):
        action = action.strip()
        if action.find("examine") == 0 or action.find("inspect") == 0:
            action = action[7:]
        elif action.find("x") == 0:
            action = action[1:]
        elif action.find("describe") == 0:
            action = action[8:]
        elif action.find("check") == 0:
            action = action[5:]
        action = action.strip()
        if action == "":
            print("What do you want to examine?")
            action = input("> ").lower()
        action = action.strip()
    '''
    if "examine" in actiontype:
        if part == "grassy_field":
            if action == "grass" or action == "field" or action == "brush":
                print(" There seems to be purple particles emanating from the grass.")
            elif action in mineshaftdict:
                print(" You would have to get closer to see it.")
            else:
                print(" We don't know what you are trying to examine.")
        elif part == "cabin_living_room":
            if action in fireplacedict:
                print('It seems odd that fireplace was lit before you got here.')
            elif action == "table" or action == "dining table":
                print("You notice a key on the table.")
            else:
                print(" We don't know what you are trying to examine.")
        elif part == "cabin_1st_floor_bathroom":
            if action == "shower":
                print("The shower curtains appear to be closed. You can see a silhouette of a person behind the curtain.")
            else:
                print(" We don't know what you are trying to examine.")
        elif part == "cavepart1":
            if action == "light" or action == "feint light" or action == "glow" or action == "feint glow" or action == "glowing light":
                if paratype == 1:
                    print(fill(" The feint white light continues to grow brighter as you continue down the\ntunnel."))
                elif paratype == 2:
                    print(" The feint white light continues to grow brighter as you continue down the tunnel.")
            elif action == "sulfur" or action == "smell of sulfur" or action == "smell sulfur" or action == "sulfur smell":
                print(" There is a smell of sulfur in the air coming from down the tunnel.")
            else:
                print(" We don't know what you are trying to examine.")
        elif part == "cavepart2":
            if action == "torch" or action == "flame" or action == "fire" or action == "light":
                if paratype == 1:
                    print(" The wood burning torch seems to be perfectly block shaped and the flame\nis red with tiny white sparks flying off and little particles of smoke.")
                if paratype == 2:
                    print(" The wood burning torch seems to be perfectly block shaped and the flame is red with tiny white sparks flying off and little particles of smoke.")
            else:
                print(" We don't know what you are trying to examine.")
                
        elif part == "cavepart2_r1":
            if action == "imp":
                if enemiesalive["cavepart2_r1_imp"] == 1:
                    print("HP: " + str(npcstats["health_cavepart2_r1_imp"]))
                    print("Attack: " + str(npcstats["attack_cavepart2_r1_imp"]))
                    print("Defence: " + str(npcstats["defence_cavepart2_r1_imp"]))
        else:
            print("There is nothing to examine here.")
        done = 1


class movement():
    global tp
    global move
    global leftright
    global enter
    global leave
    global goto
    global goback
    global gobackto
    
    
    def tp():
        #Makes all the variables in the function global
        global action
        global generalpart
        global part
        global description
        global done
        if inventory["portal_gun"] == 1:
            if "teleport" in actiontype:
                if action in grassyfielddict:
                    part = "grassy_field"
                    description = 1
                if action in cabindict:
                    part = "cabin_front"
                    description = 1
                if action == "attic":
                    part = "cabin_attic"
                    description = 1
                if action == "cave":
                    part = "mineshaft_entrance"
                    description = 1
                if action == "simpsons":
                    generalpart = "simpsons_house"
                    part = "simpsons_house_front"
                    description = 1
                done = 1
    
    #Function to check if the action is a movement command, and then if
    #true, makes you move in the specified direction
    def move():
        #Makes all the variables in the function global
        global action
        global part
        global description
        global done
        global yesornoaction
        
        #Determines if the action is a movement command
        if "move" in actiontype:
            #Determines if the direction is north
            if action == "n" or action == "north":
                if part == "grassy_field":
                    part = "forestpart1"
                    description = 1
                else:
                    print('You cant go that way!')
                done = 1
            #Determines if the direction is east
            elif action == "e" or action == "east":
                if part == "mineshaft_entrance":
                    part = "grassy_field"
                    description = 1
                elif part == "cavepart1":
                    part = "mineshaft_entrance"
                    description = 1
                elif part == "cavepart2":
                    part = "cavepart1"
                    description = 1
                else:
                    print('You cant go that way!')
                done = 1
            #Determines if the direction is south
            elif action == "s" or action == "south":
                if part == "forestpart1":
                    part = "grassy_field"
                    description = 1
                else:
                    print('You cant go that way!')
                done = 1
            #Determines if the direction is west 
            elif action == "w" or action == "west":
                if part == "grassy_field":
                    part = "mineshaft_entrance"
                    description = 1
                elif part == "mineshaft_entrance":
                    part = "cavepart1"
                    yesornoaction = 0
                    description = 1
                elif part == "cavepart1":
                    part = "cavepart2"
                    description = 1
                else:
                    print('You cant go that way!')
                done = 1
            #Determines if the direction is northeast
            northeastdict = set(["ne", "n e", "n-e", "northeast", "north east", "north-east"])
            if action in northeastdict:
                print('You cant go that way!')
                done = 1
            #Determines if the direction is southeast
            southeastdict = set(["se", "s e", "s-e", "southeast", "south east", "south-east"])
            if action in southeastdict:
                if part == "grassy_field":
                    part = "cabin_front"
                    description = 1
                else:
                    print('You cant go that way!')
                done = 1
            #Determines if the direction is southwest
            southwestdict = set(["sw", "s w", "s-w", "southwest", "south west", "south-west"])
            if action in southwestdict:
                print('You cant go that way!')
                done = 1
            #Determines if the direction is northwest
            northwestdict = set(["nw", "n w", "n-w", "northwest", "north west", "north-west"])
            if action in northwestdict:
                if part == "cabin_front":
                    part = "grassy_field"
                    description = 1
                else:
                    print('You cant go that way!')
                done = 1
            
    def leftright():
        #Makes all the variables in the function global
        global action
        global part
        global description
        global done
        global yesornoaction
        #Determines if the direction is left
        if "left" in actiontype:
            if part == "cavepart2":
                part = "cavepart2_l1"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is right
        elif "right" in actiontype:
            if part == "cavepart2":
                part = "cavepart2_r1"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
    
    def enter():
        #Makes all the variables in the function global
        global action
        global part
        global description
        global done
        global yesornoaction
        global isfloornumberaction
        global isjustfloornumberaction
        global specificaction
        global isjustspecificaction
        
        action2 = "enter"
        def entererror():
            print('We dont know what your trying to ' + action2 + '.')
            
        #Determines if the action is to go inside
        if "enter" in actiontype:
            if 1 == 1:
                
                for item in set(list(floor1dict) + list(floor2dict) + list(floor3dict)):
                    if item in action:
                        if item in floor1dict:
                            isfloornumberaction = 1
                        elif item in floor2dict:
                            isfloornumberaction = 2
                        elif item in floor3dict:
                            isfloornumberaction = 3
                        action = action[:action.find(item)] + action[action.find(item) + len(item) + 1:]
                        if action == "":
                            isjustfloornumberaction = 1
                        done = done + 1
                if done > 1:
                    print("You typed to many floors.")
                    return
                done = 0
                
                for item in cabindict:
                    if action.find(item) == 0 and action[len(item):len(item) + 1] in spaceafteractiondict:
                        if item in cabindict:
                            specificaction = 1
                        action = action[:action.find(item)] + action[action.find(item) + len(item) + 1:]
                        if action == "":
                            isjustspecificaction = 1
                        break
                    
                if part != "cabin_front" and part != "simpsons_house_front" and action == "building":
                    print("We don't know what building your tring to enter.")
                    
                elif part == "cabin_front":
                    if action == "" or action == "building" or (specificaction == 1 and isjustspecificaction == 1):
                        if inventory["cabin_key"] == 1 and lockeddoors["cabin_front_door"] == 1:
                            print(fill("You will have to unlock the door first."))
                        elif inventory["cabin_key"] == 0 and lockeddoors["cabin_front_door"] == 1:
                            print(fill("It seems to be locked. You will require a key to unlock the door."))
                        elif lockeddoors["cabin_front_door"] == 0:
                            part = "cabin_living_room"
                            description = 1
                    else:
                        entererror()
                elif part == "cabin_living_room":
                    if action in bathroomdict and isfloornumberaction < 2 and specificaction < 2:
                        part = "cabin_1st_floor_bathroom"
                        description = 1
                    elif action in bedroomdict and isfloornumberaction < 2 and specificaction < 2:
                        part = "cabin_1st_floor_bedroom"
                        description = 1
                    else:
                        entererror()
                elif part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom":
                    if action in livingroomdict and isfloornumberaction < 2 and specificaction < 2:
                        part = "cabin_living_room"
                        description = 1
                    else:
                        entererror()
                elif specificaction == 1:
                    print("There is no cabin here.")
                    
                elif part == "simpsons_house_front":
                    if action in livingroomdict:
                        part = "simpsons_house_living_room"
                        
                else:
                    entererror()
            elif done == 0:
                print("There is no " + action + " to " + action2 + " here.")
            done = 1                    
    
    def leave():
        #Makes all the variables in the function global
        global action
        global part
        global description
        global done
        global yesornoaction
        
        def exiterror():
            print('We dont know what your trying to exit.')
            
        #Determines if the action is to exit room
        if "leave" in actiontype:
            if part == "cabin_living_room" and (action in "livingroomdict" or action in "cabindict" or action == ""):
                part = "cabin_front"
                description = 1
            elif part == "cabin_1st_floor_bathroom" and (action in bathroomdict or action == ""):
                part = "cabin_living_room"
                description = 1
            elif part == "cabin_1st_floor_bedroom" and (action in bedroomdict or action == ""):
                part = "cabin_living_room"
                description = 1
            else:
                exiterror()
                    
            '''else:
                print('You cant go that way!')
                '''
            done = 1
    
    def goto():
        #Makes all the variables in the function global
        global random_require_string
        global random_need_to_string
        global random_unlock_string
        
        global action
        global generalpart
        global part
        global description
        global done
        global yesornoaction
        global isfloornumberaction
        global isjustfloornumberaction
        global specificaction
        global isjustspecificaction
        
        def gotoerror():
            if action in gotoupstairsdict:
                print("You can't go upstairs here.")
            elif action in gotodownstairsdict:
                print("You can't go downstairs here.")
            else:
                print("We don't know where your trying to go to.")
            
        if "go to" in actiontype:
            
            for item in set(list(floor1dict) + list(floor2dict) + list(floor3dict)):
                if item in action:
                    if item in floor1dict:
                        isfloornumberaction = 1
                    elif item in floor2dict:
                        isfloornumberaction = 2
                    elif item in floor3dict:
                        isfloornumberaction = 3
                    action = action[:action.find(item)] + action[action.find(item) + len(item) + 1:]
                    if action == "":
                        isjustfloornumberaction = 1
                    done = done + 1
            if done > 1:
                print("You typed to many floors.")
                return
            done = 0
            
            for item in cabindict:
                if action.find(item) == 0 and action[len(item):len(item) + 1] in spaceafteractiondict:
                    if item in cabindict:
                        specificaction = 1
                    action = action[:action.find(item)] + action[action.find(item) + len(item) + 1:]
                    if action == "":
                        isjustspecificaction = 1
                    break
                        
            if (part == "cabin_front" or part == "mineshaft_entrance" or part == "forestpart1") and action in grassyfielddict and specificaction == 0:
                part = "grassy_field"
                description = 1
            
            elif part == "grassy_field" and specificaction == 1 and isjustspecificaction == 1:
                part = "cabin_front"
                description = 1
            elif part == "grassy_field" and specificaction == 0:
                if action in grassyfielddict:
                    print("You are already at the grassy field.")
                elif action in mineshaftdict:
                    part = "mineshaft_entrance"
                    description = 1
                elif action in forestdict:
                    part = "forestpart1"
                    description = 1
                else:
                    gotoerror()
            elif part == "cabin_living_room" or part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom" or part == "cabin_kitchen":
                if action in livingroomdict and isfloornumberaction < 2 and specificaction < 2:
                    if part != "cabin_living_room":
                        part = "cabin_living_room"
                        description = 1
                    else:
                        print("You are already in the " + action + ".")
                elif action in bathroomdict and isfloornumberaction < 2 and specificaction < 2:
                    if part != "cabin_1st_floor_bathroom":
                        part = "cabin_1st_floor_bathroom"
                        description = 1
                    else:
                        print("You are already in the " + action + ".")
                elif action in bedroomdict and isfloornumberaction < 2 and specificaction < 2:
                    if part != "cabin_1st_floor_bedroom":
                        part = "cabin_1st_floor_bedroom"
                        description = 1
                    else:
                        print("You are already in the " + action + ".")
                elif (isfloornumberaction == 2 and isjustfloornumberaction == 1 and specificaction < 2) or (action in gotoupstairsdict and isfloornumberaction == 0 and specificaction == 0):
                    part = "cabin_2nd_floor_bedroom_connecter"
                    description = 1
                    
                #TODO
                # elif action in kitchendict:
                    # part = "cabin_kitchen"
                    # description = 1
                else:
                    gotoerror()
            elif part == "cabin_2nd_floor_bedroom_connecter":
                if (isfloornumberaction < 2 and (action in livingroomdict or (action[:6] == "cabin " and action[6:] in livingroomdict))) or (isfloornumberaction == 1 and isjustfloornumberaction == 1) or action in gotodownstairsdict or "go downstairs" in actiontype:
                    part = "cabin_living_room"
                    description = 1
                elif isfloornumberaction == 1 and action in bathroomdict:
                    part = "cabin_1st_floor_bathroom"
                    description = 1
                elif isfloornumberaction == 1 and action in bedroomdict:
                    part = "cabin_1st_floor_bedroom"
                    description = 1
                elif isfloornumberaction == 1 and action in kitchendict:
                    part = "cabin_kitchen"
                    description = 1
                #TODO
                # elif action in bathroomdict:
                    # part = "cabin_2nd_floor_bathroom"
                    # description = 1
                elif action == "attic":
                    if changableobjects["cabin_attic_ladder_placed"] == 1 and lockeddoors["cabin_attic_hatch"] == 0:
                        part = cabin_attic
                        description = 1
                    elif changableobjects["cabin_attic_ladder_placed"] == 1 and lockeddoors["cabin_attic_hatch"] == 1:
                        random_num = random.randint(1,2)
                        if random_num == 1:
                            print(fill("You will " + random_require_string + " a key to " + random_unlock_string + " the cabin attic hatch."))
                        elif random_num == 2:
                            print(fill("You will " + random_need_to_string + " to unlock the cabin attic hatch first."))
                    elif changableobjects["cabin_attic_ladder_placed"] == 0:
                        print(fill("You will " + random_require_string + " a ladder to reach the attic."))
                    elif inventory["ladder"] == 1:
                        print(fill("You will " + random_need_to_string + " to place a ladder to access the attic."))
                else:
                    gotoerror()
            elif generalpart == "simpsons_house" and action == "simpsons home":
                print("You are already at the Simpsons home.")
            elif generalpart == "springfield_school" and action == "simpsons school":
                print("You are already at the Springfield Elementary School.")
            elif generalpart == "kwik_e_mart" and action == "kwik_e_mart":
                print("You are already at the Kwik-E-Mart.")
            elif part == "simpsons_house_front" or part == "springfield_school" or part == "kwik_e_mart":
                if action == "simpsons home":
                    generalpart = "simpsons_house"
                    part = "simpsons_house_front"
                    description = 1
                elif action == "simpsons school":
                    generalpart = "springfield_school"
                    part = "springfield_school_front"
                    description = 1
                elif action == "kwik-e-mart":
                    generalpart = "kwik_e_mart"
                    part = "kwik_e_mart_front"
                    description = 1
                else:
                    gotoerror()
            elif "go upstairs" in actiontype:
                print("You can't go upstairs here.")
            elif "go downstairs" in actiontype:
                print("You can't go downstairs here.")
            else:
                gotoerror()
            done = 1
    
    def goback():
        #Makes all the variables in the function global
        global actiontype
        global action
        global part
        global description
        global done
        global yesornoaction
        if "go back" in actiontype:
            if len(previouspart) > 1:
                part = previouspart[-2]
                previouspart.pop(-1)
                description = 1
            else:
                print("There is nothing to go back to.")
            done = 1
            '''
            if part == "cavepart1":
                part = "mineshaft_entrance"
                description = 1
            elif part == "cavepart2":
                part = "cavepart1"
                description = 1
            elif part == "cavepart2_l1" or part == "cavepart2_r1":
                part = "cavepart2"
                description = 1
            else:
                print("We don't know what your tring to go back to.")
            '''
    
    def gobackto():
        if part != previouspart[-1]:
            previouspart.append(part)
        
    '''
    def goupstairs():
        #Makes all the variables in the function global
        global action
        global part
        global description
        global done
        global yesornoaction
        #Determines if the action is to go inside
        if "go upstairs" in actiontype:
            if part == "cabin_living_room" or part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom" or part == "cabin_kitchen":
                # print("You go upsatirs and enter the cabin upper floor.")
                part = "cabin_2nd_floor_bedroom_connecter"
                description = 1
            else:
                print("You can't go upstairs here.")
            done = 1
        if "go downstairs" in actiontype:
            if part == "cabin_2nd_floor_bedroom_connecter":
                # print("You go downstairs and enter the cabin living room.")
                part = "cabin_living_room"
                description = 1
            else:
                print("You can't go downstairs here.")
            done = 1
    '''

#Function to check if the action is a unlock command, and then if
#true, unlocks the specified object/door
def dosomethingwithsomething():
    #Makes all the variables in the function global
    global action
    global action2
    global actiontype
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global dialogschosen
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    usedict = set(["use"])
    unlockdict = set(["unlock"])
    putoutdict = set(["put out"])
    keydict = set(["key"])
    waterbucketdict = set(["bucket", "water bucket"])
    itemstousedict = set(list(keydict) + list(waterbucketdict))
    thingstousekeysondict = set(["door", "to unlock door"])
    thingstousewaterondict = set(list(fireplacedict))
    thingstouseitemsondict = set(list(thingstousekeysondict) + list(fireplacedict))
    
    usekeyondoordict = set(["door", "to unlock door"])
    
    itemtouse = ""
    useitemonaction = ""
    
    if action.find("unlock") == 0 and action[6:7] in spaceafteractiondict:
        action = action[7:]
        actiontype = set(["use item"])
        itemtouse = "key"
        if action == "":
            print(fill("What would you like to unlock?"))
            useitemonaction = input(">").lower()
            useitemonaction = useitemonaction.strip()
        else:
            useitemonaction = action
        if useitemonaction not in thingstousekeysondict and useitemonaction in thingstouseitemsondict:
            print(fill("You can't unlock that."))
            done = 1
            return
        elif useitemonaction not in thingstouseitemsondict:
            print(fill("We don't know what your trying to unlock."))
            done = 1
            return
        
    itemschecked = 0
    if action.find("put out") == 0 and action[7:8] in spaceafteractiondict:
        action = action[8:]
        action = action.strip()
        actiontype = set(["use item"])
        if action == "":
            print(fill("What would you like to put out?"))
            action = input(">").lower()
            action = action.strip()
        if action.find("the ") == 0:
            action = action[4:]
            action = action.strip()
        for item in thingstousewaterondict:
            itemschecked += 1
            if action.find(item) == 0 and action[len(item):len(item) + 1] in spaceafteractiondict:
                itemschecked -= 1
                useitemonaction = item
                action = action[len(item) + 1:]
                if action.find("with ") == 0:
                    action = action[5:]
                    action = action.strip()
                if action == "":
                    print(fill("What would you like to use to put out the " + useitemonaction + "."))
                    action = input(">").lower()
                    action = action.strip()
                itemtouse = action
                if itemtouse not in itemstousedict:
                    print(fill("We don't know what your trying to use to put out the " + useitemonaction + "."))
                    done = 1
                    return
    if itemschecked == len(thingstousewaterondict):
        print(fill("We don't know what your trying to put out."))
        done = 1
        return
        
            
            
    if action.find(" on ") > -1:
        action = action[:action.find(" on ") + 1] + action[action.find(" on ") + 4:]
    
    itemschecked = 0
    if action.find("use ") == 0:
        action = action[4:]
        actiontype = set(["use item"])
        for item in itemstousedict:
            itemschecked += 1
            index = action.find(item)
            if action.find(item) == 0 and action[index + len(item):index + len(item) + 1] in spaceafteractiondict:
                itemschecked -= 1
                itemtouse = item
                if action == "":
                    print(fill("What do you want to use the " + item + " on?"))
                    useitemonaction = input(">").lower()
                    useitemonaction = useitemonaction.strip()
                else:
                    useitemonaction = action[:index] + action[index + len(item) + 1:]
                if useitemonaction not in thingstouseitemsondict:
                    print(fill("We don't know what your trying to use the " + itemtouse + " on."))
                    done = 1
                    return
                elif (itemtouse in keydict and useitemonaction not in thingstousekeysondict) or (itemtouse in waterbucketdict and useitemonaction not in thingstousewaterondict):
                    print(fill("You can't use a " + itemtouse + " on a " + useitemonaction + "."))
                    done = 1
                    return
                
                break
    if itemschecked == len(itemstousedict):
        print(fill("We don't know what your trying to use."))
        done = 1
        return
                

    '''
    if action == "unlock" or action == "unlock door" or action == "use key" or action == "use key on door" or action == "use key on cabin door":
    '''
    if "use item" in actiontype:
        if itemtouse in keydict:
            if useitemonaction in usekeyondoordict:
                if part == "cabin_front":
                        if inventory["cabin_key"] == 0 and lockeddoors["cabin_front_door"] == 1:
                            print("You will require a key to unlock the door.")
                        elif inventory["cabin_key"] == 1 and lockeddoors["cabin_front_door"] == 1:
                            print("You use the cabin key to unlock the front door.")
                            lockeddoors["cabin_front_door"] = 0
                            inventory["cabin_key"] = 0
                        elif lockeddoors["cabin_front_door"] == 0:
                            print("The door is already unlocked.")
                else:
                    print(fill("There isn't a " + useitemonaction + " to use a " + itemtouse + " on here."))
                done = 1
            #TODO
            #if useitemonaction in usekeyonboxdict:
                
        elif itemtouse in waterbucketdict:
            if useitemonaction in fireplacedict:
                if part == "cabin_living_room":
                        if inventory["bucket"] == 1 and inventory["water_bucket"] == 0:
                            print("You will have to fill the bucket with water first.")
                        elif inventory["water_bucket"] == 1 and inventory["bucket"] == 0:
                            print("You put out the fire with the water bucket.")
                            inventory["water_bucket"] = 0
                            inventory["bucket"] = 1
                            changableobjects["lit_cabin_fireplace"] = 0
                        elif inventory["water_bucket"] == 0 and inventory["bucket"] == 0:
                            print("You don't have a water bucket to put the fire out with.")
                
                else:
                    print("We don't know what " + useitemonaction + " your trying to put out.")
                done = 1
                
    elif action in opepcurtainsdict:
        if part == "cabin_1st_floor_bathroom":
            if "peeper" in abilities:
                print("You pull back the curtains.")
            elif "peeper" not in abilities:
                print("You will require the peeper ability to draw back the curtains.")
        else:
            print("There are no curtains to open here.")
        done = 1
        
    '''
    elif action[:12] == "put out fire" or action[:18] == "use bucket on fire":
        if action[:7] == "put out" and action[8:] in fireplacedict:
            action = action[18:]
        elif action[:12] == "put out fire":
            action = action[13:]
        if action == "":
            print("What would you like to put the fire out with?")
            action = input(">").lower()
        elif action[:4] == "with":
            action = action[5:]
        if action[:18] == "use bucket on fire":
            action = action[4:10]
        if part == "cabin_living_room":
            if action == "water bucket" or "bucket":
                if inventory["bucket"] == 1 and inventory["water_bucket"] == 0:
                    print("You will have to fill the bucket with water first.")
                elif inventory["water_bucket"] == 1 and inventory["bucket"] == 0:
                    print("You put out the fire with the water bucket.")
                    inventory["water_bucket"] = 0
                    inventory["bucket"] = 1
                    changableobjects["lit_cabin_fireplace"] = 0
                elif inventory["water_bucket"] == 0 and inventory["bucket"] == 0:
                    print("You don't have a water bucket to put the fire out with.")
            else:
                print("We don't know what your trying to put out the fire with.")
        else:
            print("We don't know what fire your trying to put out.")
        done = 1
    '''
    
    #elif action 
        
        
    '''elif action[:19] in lighttorchonfiredict or action[:18] in lighttorchonfiredict or action[:11] in lighttorchonfiredict:        
        if action[:19] in lighttorchonfiredict:
            action = action[20:]
        elif action[:18] in lighttorchonfiredict:
            action = action[19:]
        elif action[:11] in lighttorchonfiredict:
            action = action[12:]
        if action == "":
            print("What would you like to light the torch with?")
            action = input(">").lower()
        if part == "cabin_living_room" and action in fireplacedict:
            if inventory["lit_torch"] == 1 and inventory["unlit_torch"] == 0:
                print("Your torch is already lit.")
            elif inventory["lit_torch"] == 0 and inventory["unlit_torch"] == 1 and changableobjects["lit_cabin_fireplace"] == 1:
                print("You light your torch ablaze with the fireplace.")
                inventory["lit_torch"] = 1
                inventory["unlit_torch"] = 0
                
        done = 1'''
        
        

#Function to determine if a yes or no question has been asked and then
#determines if the answer was yes or no, and then acts accordingly
def yesorno():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornotype
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global dialogschosen
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    yesnodict = set(["yes", "yas", "y", "no", "nah", "n"])
    yesdict = set(["yes", "yas", "y"])
    nodict = set(["no", "nah"])
    #Determines if a yes or no question has been asked and if a valid yes or
    #no answer has been given
    if (action in yesnodict) and (yesornoaction == 1):
        #Determines if the answer was yes and then determines the part, and
        #then acts accordingly
        if action in yesdict:
            if part == "mineshaft_entrance":
                part = "cavepart1"
                description = 1
                done = 1
            elif part == "cavepart2_r1":
                yesornotype = ""
                action_of_fight()
                done = 1
        #Determines if the answer was n and then asks if the player meant no or
        #north
        elif action == "n" or action in nodict:
            if action == "n":
                print('Did you mean no or north?')
                action = input(">").lower()
            #Determines if the answer was no and then determines the part, and then
            #acts accordingly
            if action in nodict:
                if part == "mineshaft_entrance":
                    print(fill('You decide to wait a little bit before entering the cave.'))
                    part = "grassy_field"
                    description = 1
                elif part == "cavepart2_r1":
                    print(fill('You decide to not beat up the helpless imp for now however he is still blocking the right path.'))
                    yesornotype = ""
                    description = 1
                done = 1
            else:
                print("We still don't know if you mean no or north.")
        yesornoaction = 0
        done = 1

#Function to determine if it needs to ask a yes or no question and then if so,
#it asks the question depending on the part and then sets the yesornoaction
#variable to 1
def askyesorno():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornotype
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global dialogschosen
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    #When needed it asks a yes or no question, determined by the part, and
    #then sets the yesornoaction variable to 1
    if part == "mineshaft_entrance":
        print('Do you go in?')
        yesornoaction = 1
    elif part == "cavepart2_r1" and yesornotype == "fight":
        print(fill("Are you sure you want to do this?"))
        yesornoaction = 1

def talkto():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    global indialog
    global talking
    if action == "talk with rick":
        if part == "cabin_attic":
            talking = "rick"

def dialog():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global dialogschosen
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    if indialog == 1:
        if dialogpart == "rick_and_morty_apear_in_attic":
            print(fill(indent("As you go to " + action2 + " the portal gun a green portal opens up behind you and an old man with spiky white hair and a labcoat holding a flask= and identical portal gun, along with a brown haired boy wearing a yellow t-shirt and blue pants, step through the portal into the room as it dissapears behind them.")))
            print("")
            print(fill("Rick: "))
            print(fill(indent("Hi name's Rick Sanchez. Me and my ill minded companion are going to have to confinscate that portal gun. Unless you want to be converted to a pile of dung goop.")))
            #TODO Need to fill story gap
        indialog = 0
        dialogschosen = []
        dialogchoices()
        
        
def dialogchoices():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global dialogschosen
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    if dialogpart == "rick_and_morty_apear_in_attic":
        print("What do you choose to do?")
        if 1 not in dialogschosen:
            time.sleep(1)
            print("1: Grab portal gun and run")
        if 2 not in dialogschosen:
            time.sleep(1)
            print("2: Spit in Rick's face")
        if 3 not in dialogschosen:
            time.sleep(1)
            print("3: Take boy as hostage")
        if 4 not in dialogschosen:
            time.sleep(1)
            print("4: Ask if you can join them")
        time.sleep(1)
    choosedialog = 1
    done = 1
    
def chooseadialog():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    if choosedialog == 1:
        if dialogpart == "rick_and_morty_apear_in_attic":
            if action == "1" and 1 not in dialogschosen:
                print(fill(""))
                dialogschosen.append(1)
                dialogchoices()
            elif action == "2" and 2 not in dialogschosen:
                print(fill("You spit directly into Rick's face for absolutely no reason."))
                print(fill("Rick: "))
                print(fill(indent(""" "Well thats just rude." """)))
                print("")
                dialogschosen.append(2)
                dialogchoices()
            elif action == "3" and 3 not in dialogschosen:
                print(fill(""))
                dialogschosen.append(3)
                dialogchoices()
            elif action == "4":
                print(fill("Rick: "))
                print(fill(indent(""""Well I suppose we could use the help seeing as you've got this far from waking up in Grassy Field." """)))
                print(fill(""))
                print(fill("""(You wonder how he knows that)"""))
                print(fill(""))
                print(fill(indent(""""First we *buuurrrbbbb* need to get some duff beeer because *urp* I'm nearly out of boose. It coincedently helps me think. Here hop in this *urp* portal." """)))
                print(fill(""))      
                dialogschosen.append(4)
                dialogchoices()
            else:
                print("That's not a valid option.")
        done = 1
                
            
def fight():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornotype
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    if "fight" in actiontype:
        if part == "cavepart2" and enemiesalive["cavepart2_r1_imp"] == 1:
            print(fill("The imp seems to be minding his own business."))
            print("")
            
            print("You fought wronf!")
            yesornotype = "fight"
        done = 1

def action_of_fight():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    print("fude")
        
def stats():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    if action == "print stats" or action == "diagnose":
        print(healthpoints)
        print(attackpoints)
        print(defencepoints)
        done = 1
        
    

"""
#Function to determine if the action is to check an object
def checkobject():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action[:5] == "check" or action[:7] == "inspect":
        if (action[:5] == "check" and action[5:] == "") or (action [:7] == "inspect" and action[7:] == ""):
            print("What would you like to " + action + "?")
            action = input(">").lower()
        else:
            if action [:5] == "check":
                action = action[6:]
            elif action[:7] == "inspect":
                action = action[8:]
        if part == "cabin_living_room":
            if action == "table" or action == "dining table":
                print("You notice a key on the table.")
        else:
            print("We don't know what your trying to check.")
        done = 1
"""

#Function to determine if the action is to take an object
def takeobject():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    def takeobjecterror():
        print("There is no " + action + " to " + action2 + " here.")
    if "take" in actiontype:
        if action == "key" or action == "key on table":
            if part == "cabin_living_room" and changableobjects["cabin_upstairs_bedroom_key_on_table"] == 1:
                inventory["cabin_upstairs_bedroom_key"] = 1
                changableobjects["cabin_upstairs_bedroom_key_on_table"] = 0
                print("You " + action2 + " the key.")
            elif part == "cabin_living_room" and changableobjects["cabin_upstairs_bedroom_key_on_table"] == 0:
                print("You already picked up the key.")
            else:
                takeobjecterror()
        elif action == "portal gun":
            if part == "cabin_attic":
                dialogcharacter = "rick"
                dialogpart = "rick_and_morty_apear_in_attic"
                dialogspecificpart = 1
                indialog = 1
            else:
                takeobjecterror()
        elif action == "torch":
            if inventory["unlit_torch"] == 0 and inventory["lit_torch"] == 0:
                if action2 == "pick up" and part == "cavepart2":
                    print(fill("You can only pick up objects sitting on something."))
                    print(fill("Instead type: >take >snatch >grab"))
                else:
                    if part == "cavepart2":
                        inventory["unlit_torch"] = 1
                        print("As you " + action2 + " the torch of the wall the flame goes out.")
                    else:
                        takeobjecterror()
            elif inventory["unlit_torch"] == 1 or inventory["lit_torch"] == 1:
                if action2 == "pick up" and part == "cavepart2":
                    print(fill("You can only pick up objects sitting on something."))
                    print(fill("Instead: type >take >snatch >grab"))
                elif part == "cavepart2":
                    print("You already have a torch in your inventory.")
                else:
                    takeobjecterror()
        elif action == "ladder":
            if part == "cabin_front":
                if changableobjects["ladder_on_side_of_cabin"] == 1:
                    if inventory["ladder"] == 1:
                        print("You already have a " + action + ".")
                    elif inventory["ladder"] == 0:
                        changableobjects["ladder_on_side_of_cabin"] = 0
                        inventory["ladder"] = 1
                        print("You " + action2 + " the " + action + ".")
                elif changableobjects["ladder_on_side_of_cabin"] == 0:
                    print("You already took the " + action + ".")
            else:
                takeobjecterror()
                
        else:
            print("We don't know what your trying to " + action2 + ".")
        done = 1

def listcommands():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    if action == "list commands":
        print("Commands:")
        print("(Menu)")
        print(" - settings")
        print(" - save")
        print(" - load")
        print("(Info)")
        print(" - list inventory")
        print(" - list places")
        print(" - list quests")
        print("(Actions)")
        print(" - examine")
        print(" - take")
        print(" - unlock")
        done = 1

def listinventory():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    if action == "list inventory" or action == "show inventory" or action == "open inventory":
        print("Inventory: ")
        if inventory["cabin_key"] == 1:
            print(" - Cabin Key")
        if inventory["cabin_upstairs_bedroom_key"] == 1:
            print(" - Upstairs Cabin Bedroom Key")
        if inventory["water_bucket"] == 1:
            print(" - Bucket Filled With Water")
        if inventory["bucket"] == 1:
            print(" - Bucket")
        if inventory["lit_torch"] == 1:
            print(" - Torch")
        if inventory["unlit_torch"] == 1:
            print(" - Unlit Torch")
        if inventory["portal_gun"] == 1:
            print(" - Portal Gun")
        '''
        if inventory[""] == 1:
            print(" - ")
        '''
        done = 1

#Function to print a list of the places your character has discovered
def listplaces():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    printplacesdiscovered = []
    
    if action == "list places":
        if "grassy_field" in placesdiscovered:
            printplacesdiscovered.append("Grassy Field")
        if "forestpart1" in placesdiscovered:
            printplacesdiscovered.append("Forest")
        if "mineshaft_entrance" in placesdiscovered:
            printplacesdiscovered.append("Mineshaft Entrance")
        if "cavepart1" in placesdiscovered or "cavepart2" in placesdiscovered or "cavepart2_l1" in placesdiscovered or "cavepart2_r1" in placesdiscovered:
            printplacesdiscovered.append("Cave")
        if "cabin_front" in placesdiscovered:
            printplacesdiscovered.append("Cabin")
        if "simpsons_house_front" in placesdiscovered:
            printplacesdiscovered.append("Simpsons House")
            printplacesdiscovered.append("Springfield Elementary School")
            printplacesdiscovered.append("Kwik-E-Mart")
        if "springfield_school" in placesdiscovered:
            printplacesdiscovered.append("Groundskeeper Willie's Shack")
        print("Places Discovered: ")
        for item in printplacesdiscovered:
            if item == "Grassy Field":
                print("(Base Universe)")
            elif item == "Simpsons House":
                print("(Simpsons Universe)")
            print(" - " + item)
        done = 1

def listquests():
    #Makes all the variables in the function global
    global action
    global action2
    global part
    global placesdiscovered
    global printplacesdiscovered
    global description
    global done
    global yesornoaction
    global dialogcharacter
    global dialogpart
    global dialogspecificpart
    global indialog
    global choosedialog
    global healthpoints
    global attackpoints
    global defencepoints
    global questlist
    
    if action == "list quests":
        print("Quests:")
        if "simpsons_house" in placesdiscovered:
            print("(Simpsons Universe)")
            print(" Bart:")
            if questlist["get_bart_slingshot"] == 0 and questlist["get_bart_skateboard"] == 0:
                print(" - ???")
        if questlist["get_rick_duff_beer"] == 1:
            print("(Rick And Morty Universe)")
            print(" Rick:")
            print(" - Get Rick Some Duff Beer")
        done = 1
    
while True:
    done = 0
    actiontype = set([])
    randomtext()
    gobackto()
    #Calls the description printing function
    printdescription()
    isfloornumberaction = 0
    isjustfloornumberaction = 0
    specificaction = 0
    isjustspecificaction = 0
    if done == 0:
        #Calls the askyesorno function
        askyesorno()
    if done == 0:
        #Calls the dialog function
        dialog()
    if done == 0:
        #Lets you type in a action and puts the action into a variable
        action = input(">").lower()
        calculateactiontype()
    if done == 0:
        chooseadialog()
    if done == 0:
        printdescriptionaction()
    if done == 0:
        #Calls settings function
        settings()
    if done == 0:
        #Calls the save function
        save()
    if done == 0:
        #Calls the load function
        load()
    if done == 0:
        #Calls the yesorno function
        yesorno()
    if done == 0:
        #Calls the examine function
        examine()
    if done == 0:
        #Calls the teleport function
        tp()
    if done == 0:
        enter()
    if done == 0:
        #Calls the move function
        move()
    if done == 0:
        #Calls the leftright function
        leftright()
    if done == 0:
        leave()
    if done == 0:
        goto()
    if done == 0:
        goback()
    '''
    if done == 0:
        goupstairs()
    '''
    if done == 0:
        #Calls the do something with something function
        dosomethingwithsomething()
    if done == 0:
        fight()
    if done == 0:
        stats()
    if done == 0:
        #Calls the take object function
        takeobject()
    if done == 0:
        listcommands()
    if done == 0:
        #Calls the list inventory function
        listinventory()
    if done == 0:
        #Calls the list places function
        listplaces()
    if done == 0:
        #Calls the list quests function
        listquests()
    if done == 0:
        print('Thats not a valid action!')
    placesdiscovered.add(generalpart)
    placesdiscovered.add(part)

'''
Function Order:
    : enter()
    1: move()
    : leftright()
    2: goto()
'''
