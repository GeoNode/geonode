import list from './list';
import service from './service';


export default {
  getServices: list.get,
  resetServices: list.reset,
  setService: service.set,
  resetService: service.reset,
};
