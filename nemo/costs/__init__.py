# Copyright (C) 2024 Ben Elliston
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

"""Generation technology costs."""

from .aeta import (AETA2012_2030High, AETA2012_2030Low, AETA2012_2030Mid,
                   AETA2013_2030High, AETA2013_2030Low, AETA2013_2030Mid)
from .apgtr import APGTR2015, APGTR2030
from .ceem import CEEM2016_2030
from .gencost2021 import (GenCost2021_2020, GenCost2021_2030High,
                          GenCost2021_2030Low, GenCost2021_2040High,
                          GenCost2021_2040Low, GenCost2021_2050High,
                          GenCost2021_2050Low)
from .gencost2022 import (GenCost2022_2021, GenCost2022_2030_CP,
                          GenCost2022_2030_NZE2050,
                          GenCost2022_2030_NZEPost2050, GenCost2022_2040_CP,
                          GenCost2022_2040_NZE2050,
                          GenCost2022_2040_NZEPost2050, GenCost2022_2050_CP,
                          GenCost2022_2050_NZE2050,
                          GenCost2022_2050_NZEPost2050)
from .gencost2023 import (GenCost2023_2030_CP, GenCost2023_2030_NZE2050,
                          GenCost2023_2030_NZEPost2050, GenCost2023_2040_CP,
                          GenCost2023_2040_NZE2050,
                          GenCost2023_2040_NZEPost2050, GenCost2023_2050_CP,
                          GenCost2023_2050_NZE2050,
                          GenCost2023_2050_NZEPost2050)
from .gencost2024 import (GenCost2024_2030_CP, GenCost2024_2030_NZE2050,
                          GenCost2024_2030_NZEPost2050, GenCost2024_2040_CP,
                          GenCost2024_2040_NZE2050,
                          GenCost2024_2040_NZEPost2050, GenCost2024_2050_CP,
                          GenCost2024_2050_NZE2050,
                          GenCost2024_2050_NZEPost2050)
from .gencost2025 import (GenCost2025_2030_CP, GenCost2025_2030_NZE2050,
                          GenCost2025_2030_NZEPost2050, GenCost2025_2040_CP,
                          GenCost2025_2040_NZE2050,
                          GenCost2025_2040_NZEPost2050, GenCost2025_2050_CP,
                          GenCost2025_2050_NZE2050,
                          GenCost2025_2050_NZEPost2050)
from .null import NullCosts

cost_scenarios = {
    'Null': NullCosts,
    'AETA2012-in2030-low': AETA2012_2030Low,
    'AETA2012-in2030-mid': AETA2012_2030Mid,
    'AETA2012-in2030-high': AETA2012_2030High,
    'AETA2013-in2030-low': AETA2013_2030Low,
    'AETA2013-in2030-mid': AETA2013_2030Mid,
    'AETA2013-in2030-high': AETA2013_2030High,
    'CEEM2016-in2030': CEEM2016_2030,
    'GenCost2021-in2020': GenCost2021_2020,
    'GenCost2021-in2030-low': GenCost2021_2030Low,
    'GenCost2021-in2030-high': GenCost2021_2030High,
    'GenCost2021-in2040-low': GenCost2021_2040Low,
    'GenCost2021-in2040-high': GenCost2021_2040High,
    'GenCost2021-in2050-low': GenCost2021_2050Low,
    'GenCost2021-in2050-high': GenCost2021_2050High,
    'GenCost2022-in2021': GenCost2022_2021,
    'GenCost2022-in2030-CP': GenCost2022_2030_CP,
    'GenCost2022-in2030-NZE2050': GenCost2022_2030_NZE2050,
    'GenCost2022-in2030-NZE2050+': GenCost2022_2030_NZEPost2050,
    'GenCost2022-in2040-CP': GenCost2022_2040_CP,
    'GenCost2022-in2040-NZE2050': GenCost2022_2040_NZE2050,
    'GenCost2022-in2040-NZE2050+': GenCost2022_2040_NZEPost2050,
    'GenCost2022-in2050-CP': GenCost2022_2050_CP,
    'GenCost2022-in2050-NZE2050': GenCost2022_2050_NZE2050,
    'GenCost2022-in2050-NZE2050+': GenCost2022_2050_NZEPost2050,
    'GenCost2023-in2030-CP': GenCost2023_2030_CP,
    'GenCost2023-in2030-NZE2050': GenCost2023_2030_NZE2050,
    'GenCost2023-in2030-NZE2050+': GenCost2023_2030_NZEPost2050,
    'GenCost2023-in2040-CP': GenCost2023_2040_CP,
    'GenCost2023-in2040-NZE2050': GenCost2023_2040_NZE2050,
    'GenCost2023-in2040-NZE2050+': GenCost2023_2040_NZEPost2050,
    'GenCost2023-in2050-CP': GenCost2023_2050_CP,
    'GenCost2023-in2050-NZE2050': GenCost2023_2050_NZE2050,
    'GenCost2023-in2050-NZE2050+': GenCost2023_2050_NZEPost2050,
    'GenCost2024-in2030-CP': GenCost2024_2030_CP,
    'GenCost2024-in2030-NZE2050': GenCost2024_2030_NZE2050,
    'GenCost2024-in2030-NZE2050+': GenCost2024_2030_NZEPost2050,
    'GenCost2024-in2040-CP': GenCost2024_2040_CP,
    'GenCost2024-in2040-NZE2050': GenCost2024_2040_NZE2050,
    'GenCost2024-in2040-NZE2050+': GenCost2024_2040_NZEPost2050,
    'GenCost2024-in2050-CP': GenCost2024_2050_CP,
    'GenCost2024-in2050-NZE2050': GenCost2024_2050_NZE2050,
    'GenCost2024-in2050-NZE2050+': GenCost2024_2050_NZEPost2050,
    'DraftGenCost2025-in2030-CP': GenCost2025_2030_CP,
    'DraftGenCost2025-in2030-NZE2050': GenCost2025_2030_NZE2050,
    'DraftGenCost2025-in2030-NZE2050+': GenCost2025_2030_NZEPost2050,
    'DraftGenCost2025-in2040-CP': GenCost2025_2040_CP,
    'DraftGenCost2025-in2040-NZE2050': GenCost2025_2040_NZE2050,
    'DraftGenCost2025-in2040-NZE2050+': GenCost2025_2040_NZEPost2050,
    'DraftGenCost2025-in2050-CP': GenCost2025_2050_CP,
    'DraftGenCost2025-in2050-NZE2050': GenCost2025_2050_NZE2050,
    'DraftGenCost2025-in2050-NZE2050+': GenCost2025_2050_NZEPost2050,
    'PGTR2015': APGTR2015,
    'PGTR2030': APGTR2030,
}

# Compute __all__ from the above dictionary.
__all__ = [cls.__name__ for cls in cost_scenarios.values()]
