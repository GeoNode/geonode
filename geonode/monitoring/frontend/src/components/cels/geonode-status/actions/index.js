import cpu from './cpu';
import mem from './mem';


export default {
  getCpu: cpu.get,
  resetCpu: cpu.reset,
  getMem: mem.get,
  resetMem: mem.reset,
};
