"""A stub for profiling tools to run one basic simulation."""

import os
import nem
c = nem.Context()
c.track_exchanges = True
del nem.generators.Fuelled.summary
nem.run(c)
nem.plot(c, filename='foo.png')
nem.plot(c, filename='foo.png', spills=True)
os.unlink ('foo.png')
