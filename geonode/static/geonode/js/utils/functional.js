const compose = (...fns) =>
  fns
    .slice(0, fns.length - 1)
    .reduceRight((result, fn) => fn(result), fns[fns.length - 1]);

const pipe = (...fns) => compose(...fns.reverse());

const curry = (f, arr = []) => (...args) => a =>
  a.length === f.length ? f(...a) : curry(f, a)([...arr, ...args]);

const trace = (label, value) => {
  // eslint-disable-next-line no-console
  console.log(`${label}: ${value}`);
  return value;
};

const map = fn => mappable => mappable.map(fn);

export default {
  compose,
  curry,
  map,
  pipe,
  trace
};
