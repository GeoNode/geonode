import list from './list';
import service from './service';
import data from './data';


export default {
  getServices: list.get,
  resetServices: list.reset,
  setService: service.set,
  resetService: service.reset,
  getData: data.get,
  resetData: data.reset,
};
