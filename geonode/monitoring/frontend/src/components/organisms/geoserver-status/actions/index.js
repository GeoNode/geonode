import cpu from './cpu';
import memory from './memory';


export default {
  getCpu: cpu.get,
  resetCpu: cpu.reset,
  getMemory: memory.get,
  resetMemory: memory.reset,
};
