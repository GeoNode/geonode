const compose = (...fns) =>
  fns
    .slice(0, fns.length - 1)
    .reduceRight((result, fn) => fn(result), fns[fns.length - 1]);

const pipe = (...fns) => compose(...fns.reverse());

const curry = (f, arr = []) => (...args) => a =>
  a.length === f.length ? f(...a) : curry(f, a)([...arr, ...args]);

export default {
  compose,
  pipe,
  curry
};
