functions = {};

var add_function = function(fun) {
	var fun_name = arguments[0];
	functions[fun_name] = fun;
};