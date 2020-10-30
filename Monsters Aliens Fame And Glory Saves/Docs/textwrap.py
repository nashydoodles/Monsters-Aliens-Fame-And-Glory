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


def indent(text, prefix, predicate=None):
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
            yield (prefix + line if predicate(line) else line)
    return ''.join(prefixed_lines())


if __name__ == "__main__":
    #print dedent("\tfoo\n\tbar")
    #print dedent("  \thello there\n  \t  how are you?")
    print(dedent("Hello there.\n  This is indented."))



description = 1
part = "grassy_field"
done = 0
yesornoaction = 0
placesdiscovered = set([])
placesdiscovered.add(part)
printplacesdiscovered = ["Grassy Field"]
inventory = {"cabin_key":1, "cabin_upstairs_bedroom_key":0, "water_bucket":1, "bucket":0, "unlit_torch":0, "lit_torch":0}
lockeddoors = {"cabin_front_door":1}
changableobjects = {"lit_cabin_fireplace":1}
beento = {"grassy_field":0, "cavepart1":0}
paratype = 2

cabindict = set(["cabin", "log cabin", "creepy log cabin"])
bathroomdict = set(["bathroom", "bath room", "washroom", "wash room"])
bedroomdict = set(["bedroom", "bed room"])
cabinlivingroomdict = set(["cabin living room", "cabin livingroom", "living room", "livingroom", "cabin main room", "main room", "cabin lobby", "lobby"])
grassyfielddict = set(["grassy field", "field", "open field"])
mineshaftdict = set(["mineshaft", "mine shaft", "mine", "cave", "mine cave"])
forestdict = set(["forest", "woods", "tree forest"])
gotoupstairsdict = set(["upstairs", "2nd floor", "2ndfloor", "second floor", "upper floor"])
opepcurtainsdict = set(["pull back curtain", "pull back curtains", "open curtain", "open curtains", "draw back curtain", "draw back curtains"])
lighttorchonfiredict = set(["light torch on fire", "light torch ablaze", "light torch"])
fireplacedict = set(["fireplace", "fire place"])

abilities = set(["pick up"])

def save():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    global inventory
    global lockeddoors
    global changableobjects
    global beento
    if ("save" in action):
        action = action.strip()
        if action == "save":
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
            savefile = {savepart:1, saveplacesdiscovered:2, saveinventory:3, savelockeddoors:4, savechangableobjects:5, savebeento:6}
            print("Type: load " + str(savefile))
            print("In order to load your game.")
            print("You saved the game.")
            done = 1
            
def load():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    global inventory
    global lockeddoors
    global changableobjects
    global beento
    if ("load" in action):
        action = action.strip()
        action = action[5:]
        if (action[:1] == "{") and (action[-1:] == "}"):
            #Loads places discovered
            index = action.find("': 1")
            part = action[2:index]
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
            index = action.find("': 5")
            index2 = action.find("': 6")
            action2 = action[index + 8:index2]
            beento = {}    
            for index, word in enumerate(action2.split()):
                index3 = word.find(":")
                beento[word[:index3]] = int(word[index3 + 1:])
            # print(beento)
            
            print(">You loaded the game from your savefile.")
            description = 1
            done = 1

#Function to check if the action is an examine command and then determines
#what to examine and then prints the description of the examined object or
#thing
def examine():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    
    #Determines if the action is a examine command
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
        if action[1:] == "" and (part == "grassy_field" or part == "cabin_living_room" or part == "cabin_1st_floor_bathroom" or part == "cavepart1" or part == "cavepart2"):
            print("What do you want to examine?")
            action = input("> ").lower()
        action = action.strip()
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
                    print(" The feint white light continues to grow brighter as you continue down the\ntunnel.")
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
        else:
            print("There is nothing to examine here.")
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
    if ("n" in action) or ("e" in action) or ("s" in action) or ("w" in action) or ("u" in action) or ("d" in action):
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
    if "l" in action or "r" in action:
        #Determines if the direction is left
        if action == "l" or action == "left" or action == "go left":
            if part == "cavepart2":
                part = "cavepart2_l1"
                description = 1
            else:
                print('You cant go that way!')
            done = 1
        #Determines if the direction is right
        elif action == "r" or action == "right" or action == "go right":
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
    if ("go in" in action) or ("enter" in action):
        #Determines if the action is to go inside
        if "go inside" in action or "go in" in action or "enter" in action or "enter building" in action:
            if part == "cabin_front" and (action == "go inside" or action == "go in" or action == "enter" or action == "enter building"):
                if inventory["cabin_key"] == 1 and lockeddoors["cabin_front_door"] == 1:
                    print("You will have to unlock the door first.")
                elif inventory["cabin_key"] == 0 and lockeddoors["cabin_front_door"] == 1:
                    print("It seems to be locked. You will require a key to unlock the door.")
                elif lockeddoors["cabin_front_door"] == 0:
                    part = "cabin_living_room"
                    description = 1
                done = 1
            elif action[:9] == "go inside":
                action = action[10:]
            elif action[:5] == "go in" or action[:5] == "enter":
                action = action[6:]
            if action != "" and action != "go inside" and action != "go in" and action != "enter" and action != "enter building" and action not in cabindict and action not in bathroomdict and action not in bedroomdict:
                print('We dont know what your trying to enter.')
            elif part == "cabin_front" and action in cabindict and done == 0:
                if inventory["cabin_key"] == 1 and lockeddoors["cabin_front_door"] == 1:
                    print("You will have to unlock the door first.")
                elif inventory["cabin_key"] == 0 and lockeddoors["cabin_front_door"] == 1:
                    print("It seems to be locked. You will require a key to unlock the door.")
                elif lockeddoors["cabin_front_door"] == 0:
                    part = "cabin_living_room"
                    description = 1
            elif part == "cabin_living_room" and action in bathroomdict and done == 0:
                part = "cabin_1st_floor_bathroom"
                description = 1
            elif part == "cabin_living_room" and action in bedroomdict and done == 0:
                part = "cabin_1st_floor_bedroom"
                description = 1
            elif (part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom") and action in cabinlivingroomdict and done == 0:
                part = "cabin_living_room"
                description = 1
            elif action == "":
                print("What do you want to enter?")
                action = input(">").lower()
                if part == "cabin_front":
                    if action in cabindict:
                        if inventory["cabin_key"] == 1 and lockeddoors["cabin_front_door"] == 1:
                            print("You will have to unlock the door first.")
                        elif inventory["cabin_key"] == 0 and lockeddoors["cabin_front_door"] == 1:
                            print("It seems to be locked. You will require a key to unlock the door.")
                        elif lockeddoors["cabin_front_door"] == 0:
                            part = "cabin_living_room"
                            description = 1
                    else:
                        print('We dont know what your trying to enter.')
                elif part == "cabin_living_room":
                    if action in bathroomdict:
                        part = "cabin_1st_floor_bathroom"
                        description = 1
                    elif action in bedroomdict:
                        part = "cabin_1st_floor_bedroom"
                        description = 1
                    else:
                        print('We dont know what your trying to enter.')
                elif part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom":
                    if action in cabinlivingroomdict:
                        part = "cabin_living_room"
                        description = 1
                    else:
                        print('We dont know what your trying to enter.')
                
                else:
                    print('We dont know what your trying to enter.')
            done = 1                    

def leave():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if ("exit" in action) or ("leave" in action):
        #Determines if the action is to exit room
        if "exit" in action or "leave" in action:
            if part == "cabin_living_room" and (action == "exit" or action == "leave"):
                part = "cabin_front"
                description = 1
            elif (part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom") and (action == "exit" or action == "leave"):
                part = "cabin_living_room"
                description = 1
            elif action[:4] == "exit":
                action = action[5:]
            elif action[:5] == "leave":
                action = action[6:]
            if action != "" and action != "exit" and action != "leave" and action not in bathroomdict and action not in bedroomdict:
                print('We dont know what your trying to exit.')
            elif part == "cabin_living_room":
                if action == "cabin" or action == "main room" or action == "living room":
                    part = "cabin_front"
                    description = 1
            elif part == "cabin_1st_floor_bathroom":
                if action in bathroomdict:
                    part = "cabin_living_room"
                    description = 1
            elif action == "":
                print("What do you want to exit?")
                action = input(">").lower()
                if part == "cabin_living_room":
                    if action == "cabin" or action == "main room" or action == "living room":
                        part = "cabin_front"
                        description = 1
                    else:
                        print('We dont know what your trying to exit.')
                elif part == "cabin_1st_floor_bathroom":
                    if action in bathroomdict:
                        part = "cabin_living_room"
                        description = 1
                    else:
                        print('We dont know what your trying to exit.')
                else:
                    print('We dont know what your trying to exit.')
                
            '''else:
                print('You cant go that way!')
                '''
            done = 1

def goback():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action == "go back":
        if part == "cavepart1":
            part = "mineshaft_entrance"
            description = 1
        if part == "cavepart2":
            part = "cavepart1"
            description = 1
        if part == "cavepart2_l1" or part == "cavepart2_r1":
            part = "cavepart2"
            description = 1

def goto():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action[:5] == "go to":
        if action[:5] == "go to":
            action = action [6:]
        if action == "":
            print("Where do you want to go to?")
            action = input(">").lower()
        if (part == "cabin_front" or part == "mineshaft_entrance" or part == "forestpart1") and action in grassyfielddict:
            part = "grassy_field"
            description = 1
        elif part == "grassy_field":
            if action in mineshaftdict:
                part = "mineshaft_entrance"
                description = 1
            if action in forestdict:
                part = "forestpart1"
                description = 1
            if action in cabindict:
                part = "cabin_front"
                description = 1
        elif part == "cabin_living_room":
            if action in bathroomdict:
                part = "cabin_1st_floor_bathroom"
                description = 1
            elif action in bedroomdict:
                part = "cabin_1st_floor_bedroom"
                description = 1
            elif action in gotoupstairsdict:
                part = "cabin_2nd_floor_bedroom_connecter"
                description = 1
        done = 1

def goupstairs():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action == "go upstairs" or action == "go downstairs" or (action[:5] == "go to" and action[6:] in cabinlivingroomdict):
        #Determines if the action is to go inside
        if action == "go upstairs":
            if part == "cabin_living_room":
                part = "cabin_2nd_floor_bedroom_connecter"
                description = 1
                done = 1
        elif action == "go downstairs" or (action[:5] == "go to" and action[6:] in cabinlivingroomdict):
            if part == "cabin_2nd_floor_bedroom_connecter":
                part = "cabin_living_room"
                description = 1
                done = 1

#Function to check if the action is a unlock command, and then if
#true, unlocks the specified object/door
def dosomethingwithsomething():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action == "unlock" or action == "unlock door" or action == "use key" or action == "use key on door" or action == "use key on cabin door":
        if action[6:] == "" or action == "use key":
            print("What would you like to unlock?")
            action = input(">").lower()
        elif action[7:] == "door" or action[7:] == "cabin door":
            action = action[7:]
        elif action[11:] == "door" or action[11:] == "cabin door":
            action = action[11:]
        if part == "cabin_front":
            if action == "door" or action == "cabin door":
                if inventory["cabin_key"] == 0 and lockeddoors["cabin_front_door"] == 1:
                    print("You will require a key to unlock the door.")
                elif inventory["cabin_key"] == 1 and lockeddoors["cabin_front_door"] == 1:
                    print("You use the cabin key to unlock the front door.")
                    lockeddoors["cabin_front_door"] = 0
                    inventory["cabin_key"] = 0
                elif lockeddoors["cabin_front_door"] == 0:
                    print("The door is already unlocked.")
        else:
            print("We don't know what your trying to unlock.")
        done = 1
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
    elif action in opepcurtainsdict:
        if part == "cabin_1st_floor_bathroom":
            if "peeper" in abilities:
                print("You pull back the curtains.")
            elif "peeper" not in abilities:
                print("You will require the peeper ability to draw back the curtains.")
        else:
            print("There are no curtains to open here.")
        done = 1
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
    global part
    global description
    global done
    global yesornoaction
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
        #Determines if the answer was n and then asks if the player meant no or
        #north
        elif action == "n":
            print('Did you mean no or north?')
            action = input(">").lower()
        #Determines if the answer was no and then determines the part, and then
        #acts accordingly
        if action in nodict:
            if part == "mineshaft_entrance":
                print('You decide to wait a little bit before entering the cave.')
                part = "grassy_field"
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
    global part
    global description
    global done
    global yesornoaction
    #When needed it asks a yes or no question, determined by the part, and
    #then sets the yesornoaction variable to 1
    if part == "mineshaft_entrance":
        print('Do you go in?')
        yesornoaction = 1
        
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
    global part
    global description
    global done
    global yesornoaction
    if action[:4] == "take" or action[:6] == "snatch":
        if action[:4] == "take":
            action = action[5:]
        elif action[:6] == "snatch":
            action = action[7:]
        if action == "":
            print("What do you want to take?")
            action = input("> ").lower()
        if action == "key" or action == "key on table":
            if part == "cabin_living_room":
                inventory["cabin_upstairs_bedroom_key"] = 1
                print("You pick up the key.")
        elif action == "torch":
            if part == "cavepart2":
                inventory["unlit_torch"] = 1
                print("As you snatch the torch of the wall the flame goes out.")
        done = 1

def listcommands():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    if action == "list commands":
        print("Commands:")
        print(" - save")
        print(" - load")
        print(" - list places")
        print(" - examine")
        print(" - take")
        print(" - unlock")
        done = 1
    
#Function to print a description of your surroundings when you enter a new location
def printdescription():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
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
        elif part == "cabin_front" or part == "cabin_living_room" or part == "cabin_1st_floor_bathroom" or part == "cabin_1st_floor_bedroom" or part == "cabin_2nd_floor_bedroom_connecter":
            print('CABIN')
        '''
        elif part == "cabin_living_room":
            print('CABIN')
            print('-LIVING ROOM')
        '''
        if paratype == 1:
            if description == 1:
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
                    
        elif paratype == 2:
            if description == 1:
                if part == "grassy_field" and beento["grassy_field"] == 0:
                    print(fill('  You awaken in a grassy field surrounded by mountains. You have no idea who you are or how you got here.\n'))
                    beento["grassy_field"] = 1
                    
                if part == "grassy_field":
                    print(fill('  There looks to be a mineshaft far off into the distance, tunneling into one of the mountains, to the west. There is also a creepy old looking log cabin to the south east and a forest to the north.'))
                
                if part == "forestpart1":
                    print(fill('  You walk into a forest.'))
                
                if part == "cabin_front":
                    print(fill('  You stand at the front entrance of the creepy log cabin.'))
                
                if part == "cabin_living_room":
                    print(fill('  In the living room there is a table in the middle and a lit fireplace.'))
                
                if part == "cabin_1st_floor_bathroom":
                    print(fill('  You enter the bathroom.'))
                    
                if part == "cabin_2nd_floor_bedroom_connecter":
                    print(fill('  You go upstairs and come to a hallway bedroom connecter. You notice several closed doors, a bedroom door, a bathroom door, and a attic hatch on the ceiling.'))
                    
                if part == "mineshaft_entrance":
                    print(fill('  You stand at the entrance to the mineshaft. All you can see is darkness, and you smell the strong stench of sulfur emanating from the cave.'))
                
                if part == "cavepart1" and beento["cavepart1"] == 0:
                    print(fill('  You are now in the pitch black cave. You are surrounded by darkness, but there is a faint light coming from down the tunnel. The smell of sulfur has gotten stronger although their is now a new stench, it smells of decaying meat. If you decide to go further into the tunnel like cave, go west.'))
                    beento["cavepart1"] = 1
                    
                elif part == "cavepart1":
                    print(fill('  You are in the pitch black cave. You are surrounded by darkness, but there is a faint light coming from down the tunnel. There is a strong smell of sulfur and decaying meat. If you decide to go further into the tunnel like cave, go west.'))
                
                if part == "cavepart2":
                    print(fill('  As you continue further into the cave the potent smells continue to get stronger and stronger, however the light at the end of the tunnel proceeds to grow brighter. Eventually you come to a branching split in the cave where there are two tunnels, one to the left and one to the right. As you decide which way to go you notice something you havent noticed before. Being so caught up in thinking about where the tunnel leads, you look around and notice that everything as become very block like, almost as if your mind has lost the ability to perceive slopes, spheres or angles. You also notice where the light has been coming from this whole time as there is an also block like torch pinned to the wall between the two branching paths.'))
                
                if part == "cavepart2_l1":
                    print(fill('  You decide to travel down the left tunnel which eventually starts too open up into a large room filled with mine carts and bright block like torches. You also notice people but they aren\'t normal people, NO! They are all blocky, their arms, their legs, even their heads!'))
                    
        description = 0
        done = 1

#Function to print a list of the places your character has discovered
def listplaces():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
    global placesdiscovered 
    global printplacesdiscovered
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
        print("Places Discovered: ")
        for item in printplacesdiscovered:
            print(" - " + item)
        done = 1

def listinventory():
    #Makes all the variables in the function global
    global action
    global part
    global description
    global done
    global yesornoaction
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
        done = 1
    
while True:
    done = 0
    #Calls the description printing function
    printdescription()
    if done == 0:
        #Calls the askyesorno function
        askyesorno()
    if done == 0:
        #Lets you type in a action and puts the action into a variable
        action = input(">").lower()
    if done == 0:
        #Calls the list places function
        listplaces()
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
        #Calls the move function
        move()
    if done == 0:
        #Calls the leftright function
        leftright()
    if done == 0:
        enter()
    if done == 0:
        leave()
    if done == 0:
        goback()
    if done == 0:
        goto()
    if done == 0:
        goupstairs()
    if done == 0:
        #Calls the do something with something function
        dosomethingwithsomething()
    if done == 0:
        #Calls the take object function
        takeobject()
    if done == 0:
        #Calls the list inventory function
        listinventory()
    if done == 0:
        listcommands()
    if done == 0:
        print('Thats not a valid action!')
    placesdiscovered.add(part)



