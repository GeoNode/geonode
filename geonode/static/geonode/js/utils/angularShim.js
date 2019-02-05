import functional from "app/utils/functional";

export default {
  syncScope: functional.curry((mapping, $scope, obj2) => {
    for (let i = 0; i < mapping.length; i += 1) {
      if (typeof obj2.get([mapping[i][1]]) === "object") {
        $scope[mapping[i][0]] = { ...obj2.get([mapping[i][1]]) };
      } else {
        $scope[mapping[i][0]] = obj2.get([mapping[i][1]]);
      }
    }
    setTimeout(() => {
      if (!$scope.$$phase) {
        $scope.$apply();
      }
    });
  })
};
