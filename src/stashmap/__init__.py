# MIT License
#
# Copyright (c) 2025 Pao Corrales
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the next
# paragraph) shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Add a docstring here for the init module.

This might include a very brief description of the package,
its purpose, and any important notes.
"""

# Expose parsing utilities (import implementations directly)
from .parse_namelist import read_namelist
from .parse_namelist import write_namelist
from .parse_namelist import export_sections_to_csv
from .parse_profile import describe_variable
from .parse_profile import describe_profiles


# Expose core section classes
from .parse_core import (
	BaseSection,
	Variable,
	TimeProfile,
	DomainProfile,
	UseProfile,
	OutputStream,
)

__all__ = [
	'read_namelist',
	'write_namelist',
    'export_sections_to_csv',
	'describe_variable',
	'describe_profiles',
	'BaseSection',
	'Variable',
	'TimeProfile',
	'DomainProfile',
	'UseProfile',
	'OutputStream',
]

