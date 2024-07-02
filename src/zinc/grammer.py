class ZincGrammar:
    @staticmethod
    def is_unit_char(c: str) -> bool:
        return (
            ZincGrammar.is_alpha(c)
            or c == "%"
            or c == "_"
            or c == "/"
            or c == "$"
            or ord(c) > 128
        )

    @staticmethod
    def is_unit(s: str) -> bool:
        for i in range(0, len(s)):
            if not ZincGrammar.is_unit_char(s[i]):
                return False

        return True

    @staticmethod
    def is_alpha_lo(c: str) -> bool:
        return ord("a") <= ord(c) <= ord("z")

    @staticmethod
    def is_alpha_hi(c: str) -> bool:
        return ord("A") <= ord(c) <= ord("Z")

    @staticmethod
    def is_alpha(c: str) -> bool:
        return ZincGrammar.is_alpha_lo(c) or ZincGrammar.is_alpha_hi(c)

    @staticmethod
    def is_digit(c: str) -> bool:
        return ord("0") <= ord(c) <= ord("9")

    @staticmethod
    def is_positive_number_sign(c: str) -> bool:
        return c == "+"

    @staticmethod
    def is_negative_number_sign(c: str) -> bool:
        return c == "-"

    @staticmethod
    def is_number_sign(c: str) -> bool:
        return ZincGrammar.is_negative_number_sign(
            c
        ) or ZincGrammar.is_positive_number_sign(c)

    @staticmethod
    def is_number_start(c: str) -> bool:
        return ZincGrammar.is_digit(c) or c == "-"

    @staticmethod
    def is_hex_digit(c: str) -> bool:
        return (
            ord("a") <= ord(c) <= ord("f")
            or ord("A") <= ord(c) <= ord("F")
            or ZincGrammar.is_digit(c)
        )

    @staticmethod
    def is_hex_number_part(c: str) -> bool:
        return ZincGrammar.is_hex_digit(c) or c == "_"

    @staticmethod
    def is_ref_char(c: str) -> bool:
        return (
            ZincGrammar.is_alpha(c)
            or ZincGrammar.is_digit(c)
            or c == "_"
            or c == ":"
            or c == "-"
            or c == "."
            or c == "~"
        )

    @staticmethod
    def is_id_start(c: str) -> bool:
        return ZincGrammar.is_alpha_lo(c)

    @staticmethod
    def is_id_part(c: str) -> bool:
        return ZincGrammar.is_alpha(c) or ZincGrammar.is_digit(c) or c == "_"

    @staticmethod
    def is_keyword_start(c: str) -> bool:
        return ZincGrammar.is_alpha_hi(c)

    @staticmethod
    def is_keyword_part(c: str) -> bool:
        return ZincGrammar.is_alpha(c)

    @staticmethod
    def is_ref_start(c: str) -> bool:
        return c == "@"

    @staticmethod
    def is_ref_part(c: str) -> bool:
        return ZincGrammar.is_ref_char(c)

    @staticmethod
    def is_ref_end(c: str) -> bool:
        return c == " "

    @staticmethod
    def is_symbol_start(c: str) -> bool:
        return c == "^"

    @staticmethod
    def is_symbol_part(c: str) -> bool:
        return ZincGrammar.is_ref_char(c)

    @staticmethod
    def is_str_start(c: str) -> bool:
        return c == '"'

    @staticmethod
    def is_str_escape(c: str) -> bool:
        return c == "\\"

    @staticmethod
    def is_uri_escape(c: str) -> bool:
        return c == "\\"

    @staticmethod
    def is_uri_escaped_uni(c: str) -> bool:
        return c == "u"

    @staticmethod
    def is_str_escaped_char(c: str) -> bool:
        return c in ["b", "f", "n", "r", "t", "\\", "$", '"']

    @staticmethod
    def is_str_escped_uni(c: str) -> bool:
        return c == "u"

    @staticmethod
    def is_str_end(c: str) -> bool:
        return c == '"'

    @staticmethod
    def is_uri_start(c: str) -> bool:
        return c == "`"

    @staticmethod
    def is_uri_escaped_char(c: str) -> bool:
        return c in [
            ":",
            "/",
            "?",
            "#",
            "[",
            "]",
            "@",
            "`",
            "\\",
            "&",
            "=",
            ";",
        ]

    @staticmethod
    def is_uri_end(c: str) -> bool:
        return c == "`"

    @staticmethod
    def is_whitespace(c: str) -> bool:
        return c == " " or c == "\t" or ord(c) == 0xA0

    @staticmethod
    def is_unicode_char(c: str) -> bool:
        return ord(c) >= 0x20

    @staticmethod
    def is_nan(s: str) -> bool:
        return s == "NaN"

    @staticmethod
    def is_pos_inf(s: str) -> bool:
        return s == "INF"

    @staticmethod
    def is_neg_inf(s: str) -> bool:
        return s == "-INF"

    @staticmethod
    def is_digits_start(c: str) -> bool:
        return ZincGrammar.is_digit(c)

    @staticmethod
    def is_digits_part(c: str) -> bool:
        return ZincGrammar.is_digit(c) or c == "_"
