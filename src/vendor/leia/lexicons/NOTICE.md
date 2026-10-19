# Lexicons

* `en_lexicon.txt`, `en_booster.txt`, `en_negate.txt`: the VADER lexicon and word lists, as shipped in NLTK's
  `vader_lexicon` (VADER by C.J. Hutto, MIT license, https://github.com/cjhutto/vaderSentiment).
* `pt_lexicon.txt`, `pt_booster.txt`, `pt_negate.txt`: the lexicon of LeIA, a Portuguese adaptation of VADER
  (https://github.com/rafjaa/LeIA).

The scoring in `leia.tvx` follows `nltk.sentiment.vader` and LeIA step by step, including the places where LeIA's
code does something other than it says (see the comments there).
