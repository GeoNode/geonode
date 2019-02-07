/*
  Provides field aliases for content, count, and value.
*/

export default [
  {
    id: "owners",
    filter: "owner__username__in",
    alias: {
      value: "username",
      count: "count",
      content: "full_name"
    }
  },
  {
    id: "categories",
    filter: "category__identifier__in",
    elId: "layercategories",
    alias: {
      value: "identifier",
      count: "layers_count",
      content: "gn_description"
    }
  },
  {
    id: "categories",
    filter: "category__identifier__in",
    alias: {
      value: "identifier",
      count: "count",
      content: "gn_description"
    }
  },
  {
    id: "types",
    filter: "type__in",
    alias: {
      value: "id",
      count: "count",
      content: "name"
    }
  }
];
