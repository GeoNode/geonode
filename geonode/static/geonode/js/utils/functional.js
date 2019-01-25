const compose = (...fns) =>
  fns
    .slice(0, fns.length - 1)
    .reduceRight((result, fn) => fn(result), fns[fns.length - 1]);

const pipe = (...fns) => compose(...fns.reverse());

const curry = fn => {
  const curryN = (n, func) => (...args) =>
    args.length >= n
      ? func(...args)
      : curryN(n - args.length, (...innerArgs) => func(...args, ...innerArgs));

  return curryN(fn.length, fn);
};

const trace = (label, value) => {
  // eslint-disable-next-line
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
