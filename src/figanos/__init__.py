"""Outils pour produire des graphiques informatifs sur les impacts des changements climatiques."""

###################################################################################
# Apache Software License 2.0
#
# Copyright (c) 2024, Sarah-Claude Bourdeau-Goulet, Juliette Lavoie, Alexis Beaupré-Laperrière, Trevor James Smith
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################

__author__ = """Sarah-Claude Bourdeau-Goulet"""
__email__ = "bourdeau-goulet.sarah-claude@ouranos.ca"
__version__ = "0.6.0"

from . import matplotlib
from ._data import data
from ._logo import Logos
from ._testing import pitou
