var Sorter = function(dependencies) {
    this.dependencies = dependencies;
    this.visited = {};
    this.sorted = [];
};
Sorter.prototype = {
    sort: function() {
        for (var key in this.dependencies) {
            this.visit(key);
        }
        return this.sorted;        
    },
    visit: function(key) {
        if (!(key in this.visited)) {
            this.visited[key] = true;
            if (!(key in this.dependencies)) {
                throw "Missing dependency: " + key;
            }
            for (var path in this.dependencies[key]) {
                this.visit(path);
            }
            this.sorted.push(key);
        }
    }
};

var sort = function(dependencies) {
    var sorter = new Sorter(dependencies);
    return sorter.sort();
};

exports.sort = sort; 
