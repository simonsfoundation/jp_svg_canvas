FROM andrewosh/binder-base

MAINTAINER Aaron Watters <awatters@simonsfoundation.org>

USER main

RUN git clone https://github.com/simonsfoundation/jp_svg_canvas.git
RUN cd jp_svg_canvas; pip install -r requirements.txt
RUN cd jp_svg_canvas; python setup.py install
