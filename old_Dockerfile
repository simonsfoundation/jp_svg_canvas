FROM andrewosh/binder-base

MAINTAINER Aaron Watters <awatters@simonsfoundation.org>

USER main

RUN git clone https://github.com/simonsfoundation/jp_svg_canvas.git -b jupyter-widgets-base-moved repo
RUN cd repo; pip install -r requirements.txt
RUN cd repo; python setup.py install

#RUN pip install -r requirements.txt
#RUN python setup.py install

RUN jupyter nbextension enable --py --sys-prefix widgetsnbextension