"""
The fapy Package, Version 0.9
=============================

The fapy package contains Python classes and functions for downloading
FRC competition data from the FIRST API server. The fapy package
formats this data as
`pandas dataframes <http://pandas.pydata.org/pandas-docs/version/0.17.1/>`_,
JSON, or XML.

Version Notes
-------------

Version 0.9 is an alpha version that is still under development.

License
-------

Copyright (c) 2017 Stacy Irwin, All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in
      the documentation and/or other materials provided with the
      distribution.

    * Neither the name of the copyright holder nor the names of its
      contributors may be used to endorse or promote products derived
      from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

FIRST and FRC Overview
======================

The FIRST API is a hypertext transfer protocol (HTTP) server run by
FIRST, a non-profit organization that promotes enthusiasm for STEM
via high-intensity robotics competitions. The FIRST Robotics Comeptiion
(FRC), the highest level of FIRST compeitions, is for high school
students.

Using fapy
==========

Getting a FIRST API Account
---------------------------

Users must have their own FIRST API username and authoriziation token
to use fapy. Obtain a username and password by joining the FIRST API
project on
`TeamForge <https://usfirst.collab.net/sf/projects/first_community_developers/>`_.
Follow the instructions on the hompe page to join the project and
remember to keep your authorization token private.

Creating and Using the Session Object
-------------------------------------

Before calling a fapy function that retrieves data via the FIRST API,
users must create a *Session* object by calling the `Session`
constructor. The `Session` Constructor requires the username and
authorization token as arguments.::

    my_session = api.GetSession("username", "authorization_token")


Users will than pass the *Session*
object as the first argument to all subsequent calls to fapy functions.::

    schedule = api.get_schedule(my_session, event="TURING")

This way, users don't have to repeatedly type their authorization when
using fapy. Users can also specify other common parameters, such as
the data format ('dataframe', 'xml', or 'json') or competition season
(e.g., 2017) by setting attributes of the session object.

"""