//This is a helper to create ajax-backed jQUI dialog windows
Alternote.ajax_dialog = function(url, title)
{
	var dialogWin = $('<div style="display: none" title="' + title + '"></div>').appendTo("body");
	dialogWin.load(
		url,
		{},
		function(response, status, request)
		{
			dialogWin.dialog();	  
		}
	);
	
	return false; //Prevent browser from following URL
};