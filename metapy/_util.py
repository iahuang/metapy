class DebugTable:
    def __init__(self, rows, headers):
        self.rows = rows
        self.headers = headers

        self.row_widths = [len(header) for header in headers]
        self.draw_borders = True
        self.cell_pad = 1

        for r in rows:
            assert len(r) == len(self.headers)

            for c in range(len(r)):
                cell_width = len(str(r[c]))
                curr_width = self.row_widths[c]

                if curr_width < cell_width:
                    self.row_widths[c] = cell_width

    def print(self):
        out = []
        if self.draw_borders: out.append(self._make_divider())
        out.append(self._make_row(self.headers).upper())
        out.append(self._make_divider(bold=True) if self.draw_borders else "")

        for r in self.rows:
            out.append(self._make_row(r))
            if self.draw_borders: out.append(self._make_divider())

        print("\n".join(out))

    def _make_divider(self, bold=False):
        out = "=" if bold else "+"

        for width in self.row_widths:
            out += ("=" if bold else "-") * (width + self.cell_pad)
        
            out += "=" if bold else "+"
        
        return out

    def _make_row(self, row):
        out = ""

        if self.draw_borders:
            out = "|"

        for width, cell in zip(self.row_widths, row):
            cell = str(cell)
            out += self._rpad(cell, width + self.cell_pad)

            if self.draw_borders:
                out += "|"

        return out

    def _rpad(self, string, length, fill=" "):
        return string + fill*(length-len(string))
