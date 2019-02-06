/*
  An array of objects used to request data from the server to build
  search filters.
*/

// () => []
export default () =>
  [
    {
      id: "categories",
      endpoint: window.CATEGORIES_ENDPOINT,
      requestParam: "title__icontains",
      filterParam: "category__identifier__in",
      alias: "identifier"
    },
    {
      id: "groupcategories",
      endpoint: window.GROUP_CATEGORIES_ENDPOINT,
      requestParam: "name__icontains",
      filterParam: "slug",
      alias: "identifier",
      hide: true
    },
    {
      id: "regions",
      endpoint: window.REGIONS_ENDPOINT,
      requestParam: "title__icontains",
      filterParam: "regions__name__in",
      alias: "name"
    },
    {
      id: "owners",
      endpoint: window.OWNERS_ENDPOINT,
      requestParam: "title__icontains",
      filterParam: "owner__username__in",
      alias: "identifier"
    },
    {
      id: "tkeywords",
      endpoint: window.T_KEYWORDS_ENDPOINT,
      requestParam: "title__icontains",
      filterParam: "tkeywords__id__in",
      alias: "id"
    }
    // Only make the request if a page element possessing the id exists
  ].filter(req => !req.hide);
