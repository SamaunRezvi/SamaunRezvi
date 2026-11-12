# Responsive layout

GitHub strips CSS and media queries from a README, so the layout depends on plain HTML only.

Rules the README follows (all enforced by `tests/test_responsive.py`):

1. Images get a fixed pixel `width`. GitHub caps an image at the screen width, so a wide image shrinks on a phone.
2. Images that sit side by side add up to less than a wide screen, so they wrap and stack on a narrow one. The hero is 440px plus 340px.
3. Never a fixed `height` on a large image (it would distort when the width shrinks). Only small badges use `height`.
4. No percentage widths below 90, and no multi-column tables.
5. Both images in a row use `align="top"` so a stacked banner does not leave a gap.

Checked in a headless browser at 880px (desktop), 700px (tablet) and 390px (phone).
