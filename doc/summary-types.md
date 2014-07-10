for the publisherindicators more complicated summary

===============

indicators_summary: (indicator_id, indicator_summary) dict

indicator_summary: {
  results_num: float
  results_pct: float
  indicator: indicator
  tests: test list
}

indicator: {
  indicator_noformat <type 'bool'>
  indicator_subcategory_name <type 'unicode'>
  description <type 'unicode'>
  indicator_weight <type 'float'>
  longdescription <type 'unicode'>
  indicator_type <type 'unicode'>
  indicator_order <type 'int'>
  indicator_category_name <type 'unicode'> 
  indicator_ordinal <type 'bool'>
  id <type 'int'>
  name <type 'unicode'>
}

test: {
  results_num: float
  results_pct: float
  indicator: indicator
  test: test_data
}

test_data: {
  test_level <type 'int'>
  test_group <type 'unicode'>
  description <type 'unicode'>
  name <type 'unicode'>
  id <type 'int'>
}

======================

for the simpler one

======================

summary: (hierarchy_id, test_info2) dict

test_info2: {
  indicator <type 'dict'>
  results_num <type 'int'>
  results_pct <type 'float'>
  result_hierarchy <type 'int'>
  test <type 'dict'>
  condition <type 'list'>
}
