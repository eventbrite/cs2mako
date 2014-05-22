=======
cs2mako
=======

**cs2mako** is set of Python code that is used as a script to convert
your Clearsilver templates to Mako. It was purpose built, and intended for
one-time use. Once you use it to convert your templates, you will likely
need to hand-fix the output templates to make them work in your environment.

This repository is not currently maintained, as we no longer need it! (We
already converted our templates.)

LICENSE
=======

Feel free to fork this repository, but note that this software is shared under
the MIT license. In particular, we require that the attribution remain intact.

Usage
=====

Call cs2mako with no arguments to get this amazing help text:

	$ cd cs2mako
	$ python cs2mako
	No filename specified.
	Usage cs2mako [-o <output_filename>] [--nointl] [--noconv] <cs file>

The converted Mako files will still reference variablees in "hdf" dot notation:

       ${ hdf.variable.named.like.this }

You will want to replace hdf with the included hdf_emulator.py. Then over time
you can replace variables being set as emulated hdf to be some proper Python objects.
In Eventbrite's case, we use Django, so we follow Django context passing conventions.

About
=====

**cs2mako** is a streaming tokenizer, LR(1) parser, and code-generator.
It uses Python generators to emulate a threaded message-passing environment.

There are some rudimentary unit-tests, which should give you an idea of how **cs2mako** works.

