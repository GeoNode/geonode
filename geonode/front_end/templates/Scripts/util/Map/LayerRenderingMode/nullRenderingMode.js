mapModule.factory('NullRenderingMode', [
    function () {
        return function NullRenderingMode(tools) {
            this.activate = function () { };
            this.dispose = function () { };
            this.refresh = function () { };
            this.tools = tools;
        };
    }
]);