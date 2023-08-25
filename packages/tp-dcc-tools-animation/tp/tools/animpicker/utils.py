from __future__ import annotations

import re
from typing import List


def numeric_name(text: str, names: List[str]):

	def _find_missing_items():
		original_set = set(indexes_list)
		smallest_item = min(original_set)
		largest_item = max(original_set)
		full_set = set(range(smallest_item, largest_item + 1))
		return sorted(list(full_set - original_set))

	if text in names:
		text = re.sub('\\d*$', '', text)
		indexes_list = []
		for name in names:
			m = re.match('^%s(\\d+)' % text, name)
			if m:
				indexes_list.append(int(m.group(1)))
			else:
				indexes_list.append(0)
		indexes_list.sort()
		missing_indexes = _find_missing_items()
		if missing_indexes:
			_id = str(missing_indexes[0])
		else:
			_id = str(indexes_list[-1] + 1)
	else:
		_id = ''

	text += _id

	return text
