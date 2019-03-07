# Release notes.

* 0.9.4: Support ordering keys that follow lookups. Using these is at your own risk: You must ensure that you are using .select_related(), or it will trigger another database fetch for each lookup. This should only apply to the first/last instances, others will not be calculated.

* 0.9.3: Fix an issue where we have an empty object_list, but still think we have a previous page.

* 0.9.2: Fix issues with pagination boundaries when there are more than two ordering keys, and objects cross over a boundary that can only be discriminated by the last sort key.

* 0.9.1: Prevent errors when no objects in queryset.

* 0.9.0: Stop supporting page index and total item count.

* 0.8.5: Don't fail to render on empty result set.

* 0.8.3: Allow installing in Python 2.

* 0.8.1: Add description to pypi page.

* 0.8.0: First release.
