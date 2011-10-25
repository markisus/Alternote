console.log("client.js start");
var client = {};
(function() {
	client.init = function(eventid, userid) {
		client.eventid = eventid;
		client.userid = userid;
		$.getJSON("/get/" + eventid + "/", function(data) {
			client.posts = data.posts;
			client.last_element = data.last_element;
			client.voted = data.votes_and_flags.voted;
			client.flagged = data.votes_and_flags.flagged;
			//Generate HTML on the fly
			for (post_index in data.posts) {
				var post = data.posts[post_index];
				var postid = post['_id'];
				var message = post['post']; //Todo: this is sometimes called 'message' which is inconsistent
				var flags = post['flags'];
				var votes = post['votes'];
				var author_data = post['author'];
				add_post_tag(postid, message, flags, votes, author_data);
				
				var comments = post['comments'];
				for (comment_index in comments) {
					var comment = comments[comment_index];
					var commentid = comment['_id'];
					var message = comment['comment'];
					var flags = comment['flags'];
					var votes = comment['votes'];
					var author_data = comment['author'];
					add_comment_tag(postid, commentid, message, flags, votes, author_data);
				}
			}
			console.log(client);
			
			//Do not move the call to listen outside of the callback
			//You risk calling listen when client is in inconsistent state
			client.listen();
		});
	};
	
	client.listen = function(data) {
		console.log("Receiving...");
		if(data) synchronize(data);
		$.getJSON("/poll/" + client.eventid + "/" + client.last_element, client.listen);
	}
	
	//Server will give us a list of updates,
	//Apply each update to maintain consistency with the server
	var synchronize = function(actions) {
		var counter = 0;
		for(index in actions) {
			apply_action(actions[index]);
			counter += 1;
		}
		client.last_element += counter;
	};
	
	var apply_action = function(action) {
		//The action could be one of 10 cases
			//comment
			//post
			//flag post|comment
			//unflag post|comment
			//vote post|comment
			//unflag post|comment
		if (action['action'] === 'post') {
			var postid = action['postid'];
			var message = action['message'];
			var flags = 0;
			var votes = 0;
			var author_data = action['user'];
			add_post_tag(postid, message, flags, votes, author_data);
		}
		if (action['action'] === 'comment') {
			console.log("Comment...");
			var postid = action['postid'];
			var commentid = action['commentid'];
			var message = action['message'];
			var flags = 0;
			var votes = 0;
			var author_data = action['user'];
			add_comment_tag(postid, commentid, message, flags, votes, author_data);
		}
		if (action['action'] === 'vote_post') {
			console.log("Vote post...");
			var postid = action['postid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				disable_vote(postid);
			}
			var votes = $('#' + postid + ' .stats:first .votes');
			var numvotes = parseInt(votes.text(), 10);
			numvotes++;
			votes.text(numvotes);
			if (numvotes > 0) {
				$('#' + postid + ' .stats:first .votes_container').fadeTo('fast', 1);
			}
		};
		if (action['action'] === 'vote_comment') {
			console.log("Vote comment...");
			var commentid = action['commentid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				disable_vote(commentid);
			}
			var votes = $('#' + commentid + " .stats:first .votes");
			var numvotes = parseInt(votes.text(), 10);
			numvotes++;
			votes.text(numvotes);
			if (numvotes > 0) {
				$('#' + commentid + ' .stats:first .votes_container').fadeTo('fast', 1);
			}
		};
		if (action['action'] === 'unvote_post') {
			console.log("Unvote post...");
			var postid = action['postid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				enable_vote(postid);
			}
			var votes = $('#' + postid + " .stats:first .votes");
			var numvotes = parseInt(votes.text(), 10);
			numvotes--;
			votes.text(numvotes);
			if (numvotes === 0) {
				$('#' + postid + ' .stats:first .votes_container').fadeTo('fast', 0);
			}
		};
		if (action['action'] === 'unvote_comment') {
			console.log("Unvote comment...");
			var commentid = action['commentid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				enable_vote(commentid);
			}
			var votes = $('#' + commentid + " .stats:first .votes");
			var numvotes = parseInt(votes.text(), 10);
			numvotes--;
			if (numvotes === 0) {
				$('#' + commentid + ' .stats:first .votes_container').fadeTo('fast', 0);
			}
			votes.text(numvotes);
		};		
		if (action['action'] === 'flag_post') {
			console.log("Flag post...");
			var postid = action['postid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				disable_flag(postid);
				hide_flagged(postid);
			}
			var flags = $('#' + postid + " .stats:first .flags");
			var numflags = parseInt(flags.text(), 10);
			numflags++;
			flags.text(numflags);
			if (numflags > 0) {
				$('#' + postid + ' .stats:first .flags').fadeTo('fast', 1);
			}
		};
		if (action['action'] === 'flag_comment') {
			console.log("Flag comment...");
			var commentid = action['commentid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				disable_flag(commentid);
				hide_flagged(commentid);
			}
			var flags = $('#' + commentid + " .stats:first .flags");
			var numflags = parseInt(flags.text(), 10);
			numflags++;
			flags.text(numflags);
			if (numflags > 0) {
				$('#' + commentid + ' .stats:first .flags').fadeTo('fast', 1);
			}
		};		
		if (action['action'] === 'unflag_post') {
			console.log("Unflag post...");
			var postid = action['postid'];
			var userid = action['userid'];
				if (userid === client.userid) {
				enable_flag(postid);
			}
			var flags = $('#' + postid + " .stats:first .flags");
			var numflags = parseInt(flags.text(), 10);
			numflags--;
			flags.text(numflags);
			if (numflags === 0) {
				$('#' + postid + ' .stats:first .flags').fadeTo('fast', 0);
			}
		};
		if (action['action'] === 'unflag_comment') {
			console.log("Unflag comment...");
			var commentid = action['commentid'];
			var userid = action['userid'];
			if (userid === client.userid) {
				enable_flag(commentid);
			}
			var flags = $('#' + commentid + " .stats:first .flags");
			var numflags = parseInt(flags.text(), 10);
			numflags--;
			flags.text(numflags);
			if (numflags === 0) {
				$('#' + commentid + ' .stats:first .flags').fadeTo('fast', 0);
			}
		};		
	};
	
	
	client.post = function(message) {
		$.get("/post/" + client.eventid + "/" + message);
	};
	client.post_anon = function(message) {
		$.get("/anon_post/" + client.eventid + "/" + message);
	}
	
	client.comment = function(postid, message) {
		$.get("/comment/" + postid + "/" + message);
	};
	client.comment_anon = function(postid, message) {
		$.get("/anon_comment/" + postid + "/" + message);
	};
	
	client.vote_comment = function(commentid) {
		$.get("/vote/comment/" + commentid);
	};
	
	client.unvote_comment = function(commentid) {
		$.get("/unvote/comment/" + commentid);
	};
	
	client.flag_comment = function(commentid) {
		$.get("/flag/comment/" + commentid);
	};
	
	client.unflag_comment = function(commentid) {
		$.get("/unflag/comment/" + commentid);
	};
	
	client.vote_post = function(postid) {
		$.get("/vote/post/" + postid);
	};
	
	client.unvote_post = function(postid) {
		$.get("/unvote/post/" + postid);
	};
	
	client.flag_post = function(postid) {
		$.get("/flag/post/" + postid);
	};
	
	client.unflag_post = function(postid, callback) {
		$.get("/unflag/post/" + postid);
	};
	
	client.can_vote = function(objectid) {
		for (index in client.voted) {
			if (client.voted[index] === objectid) return false;
		}
		return true;
	}
	
	client.can_flag = function(objectid) {
		for (index in client.flagged) {
			if (client.flagged[index] == objectid) return false;
		}
		return true;
	}
	
	var enable_vote = function(objectid) {
			var vote = $('#' + objectid + " .actions:first > .vote");
			var unvote = $('#' + objectid + " .actions:first > .unvote");
			unvote.attr('style', 'display:none;');
			vote.removeAttr('style');
	};
	
	var disable_vote = function(objectid) {
			var vote = $('#' + objectid + " .actions:first > .vote");
			var unvote = $('#' + objectid + " .actions:first > .unvote");
			vote.attr('style', 'display:none;');
			unvote.removeAttr('style');
	};
	var enable_flag = function(objectid) {
			var flag = $('#' + objectid + " .actions:first > .flag");
			var unflag = $('#' + objectid + " .actions:first > .unflag");
			unflag.attr('style', 'display:none;');
			flag.removeAttr('style');
	};
	
	var disable_flag = function(objectid) {
			var flag = $('#' + objectid + " .actions:first .flag");
			var unflag = $('#' + objectid + " .actions:first .unflag");
			flag.attr('style', 'display:none;');
			unflag.removeAttr('style');
	};
	
	
	var add_post_tag = function(postid, message, flags, votes, author_data) {
		var posts = $('#maincol-body');
		
		var post = document.createElement('div');
		post.setAttribute('id', postid);
		post.setAttribute('class', 'post');
		
		var original_post = document.createElement('div');
		original_post.setAttribute('class', 'original-post ' + author_data['type']);
		
		var poster_img = document.createElement('img');
		poster_img.setAttribute('class', 'poster-img');
		poster_img.setAttribute('src', 'http://www.thehotpepper.com/public/style_images/thp/profile/default_thumb.png');
		poster_img.setAttribute('width', '48');
		poster_img.setAttribute('height', '48');
		
		var p = document.createElement('p');
		
		var a = document.createElement('a');
		a.setAttribute('class', 'link-blue name');
		a.setAttribute('href', '#');
		a.innerHTML = author_data['first_name'] + " " + author_data['last_name'];
		
		var message_div = document.createElement('div');
		message_div.setAttribute('class', 'message');
 
		var textNode = document.createTextNode(" " + message);
		
		var expanded_link = document.createElement('div');
		expanded_link.setAttribute('class', 'expanded-link');
		
		var meta = document.createElement('div');
		meta.setAttribute('class', 'meta');
		
		var comments = document.createElement('div');
		comments.setAttribute('class', 'comments');
		
		var comment_input = document.createElement('input');
		comment_input.setAttribute('type', 'text');
		comment_input.setAttribute('id', 'comment_input_for_' + postid);
		comment_input.setAttribute('placeholder', 'Add your comment and then press enter.');
		comment_shades = document.createElement('div');
		comment_shades.setAttribute('class', 'shades');
		comment_shades.setAttribute('id', 'shades_for_' + postid);
		comment_shades.setAttribute('style', 'opacity: .3;');
		comment_shades.anon = false;
		post.appendChild(original_post);
		original_post.appendChild(poster_img);
		original_post.appendChild(p);
		p.appendChild(message_div);
		message_div.appendChild(a);
		message_div.appendChild(textNode);
		original_post.appendChild(expanded_link);
		original_post.appendChild(meta);		
		meta.appendChild(make_post_actions(postid));
		meta.appendChild(make_stats(flags, votes));
		post.appendChild(comments);
		post.appendChild(comment_input);
		post.appendChild(comment_shades);
		
		posts.prepend(post);
		
		//Bind shades action
		$("#shades_for_" + postid).bind('click', function() {
			if (this.anon === false) {
				this.anon = true;
				$(this).fadeTo('fast', .7);
			} else {
				this.anon = false;
				$(this).fadeTo('fast', .3);
			}
		});
		//Bind comment submit action
		$("#comment_input_for_" + postid).keypress(function(event){
			if(event.which == 13) {
				event.preventDefault();
				var anon = document.getElementById("shades_for_" + postid).anon;
				var val = $(this).val();
				if(anon) {
					client.comment_anon(postid, val);
				} else {
					client.comment(postid, val);
				}
				$(this).val("");
			}
		});
		//See if post should be flagged
		if (flags >= 2) {
			hide_flagged(postid);
		}
	};


	var add_comment_tag = function(postid, commentid, message, flags, votes, author_data) {
		var comments = $('#' + postid + " .comments");
		
		var comment = document.createElement('div');
		comment.setAttribute('id', commentid);
		comment.setAttribute('class', 'comment ' + author_data['type']);
		
		var poster_img = document.createElement('img');
		poster_img.setAttribute('class', 'poster-img');
		poster_img.setAttribute('src', 'http://www.thehotpepper.com/public/style_images/thp/profile/default_thumb.png');
		poster_img.setAttribute('width', '30');
		poster_img.setAttribute('height', '30');
		
		var p = document.createElement('p');
		
		var a = document.createElement('a');
		a.setAttribute('class', 'link-blue name');
		a.setAttribute('href', '#');
		a.innerHTML = author_data['first_name'] + " " + author_data['last_name'];
		
		var message_div = document.createElement('div');
		message_div.setAttribute('class', 'message');
 
		var textNode = document.createTextNode(" " + message);
		
		var meta = document.createElement('div');
		meta.setAttribute('class', 'meta');

		comment.appendChild(poster_img);
		comment.appendChild(p);
		p.appendChild(message_div);
		message_div.appendChild(a);
		message_div.appendChild(textNode);
		comment.appendChild(meta);
		meta.appendChild(make_comment_actions(commentid));
		meta.appendChild(make_stats(flags, votes));
		comments.append(comment);
		
		//See if comment should be hidden
		if (flags >= 2) {
			hide_flagged(commentid);
		}
	};
	
	//Todo: make_post/comment_actions => make_object_actions
	var make_post_actions = function(postid) {
		var canvote = client.can_vote(postid);
		var canflag = client.can_flag(postid);
		var post_actions = document.createElement('div');
		post_actions.setAttribute('class', 'actions');
		
		var vote = document.createElement('a');
		vote.setAttribute('href', 'javascript:;');
		vote.setAttribute('class', 'vote link-light-blue');
		vote.setAttribute('onclick', 'client.vote_post("' + postid + '");');
		vote.innerHTML = 'like';
		
		var unvote = document.createElement('a');
		unvote.setAttribute('href', 'javascript:;');
		unvote.setAttribute('class', 'unvote link-light-blue');
		unvote.setAttribute('onclick', 'client.unvote_post("' + postid + '");');
		unvote.innerHTML = 'unlike';
		
		var td1 = document.createElement('div');
		td1.setAttribute('class', 'tinydot');
		td1.innerHTML = ".";
		
		var flag = document.createElement('a');
		flag.setAttribute('href', 'javascript:;');
		flag.setAttribute('class', 'flag link-light-blue');
		flag.setAttribute('onclick', 'client.flag_post("' + postid + '");');
		flag.innerHTML = 'flag';
		
		var unflag = document.createElement('a');
		unflag.setAttribute('href', 'javascript:;');
		unflag.setAttribute('class', 'unflag link-light-blue');
		unflag.setAttribute('onclick', 'client.unflag_post("' + postid + '");');
		unflag.innerHTML = 'unflag';
		
		if(canvote) {
			unvote.setAttribute('style', 'display:none;');
		} else {
			vote.setAttribute('style', 'display:none;');
		}
		
		if(canflag) {
			unflag.setAttribute('style', 'display:none;');
		} else {
			flag.setAttribute('style', 'display:none;');
		}
		
		post_actions.appendChild(vote);
		post_actions.appendChild(unvote);
		post_actions.appendChild(td1);
		post_actions.appendChild(flag);
		post_actions.appendChild(unflag);
		return post_actions;
	};
	
	var make_comment_actions = function(commentid) {
		var canvote = client.can_vote(commentid);
		var canflag = client.can_flag(commentid);
		var comment_actions = document.createElement('div');
		comment_actions.setAttribute('class', 'actions');
		
		var vote = document.createElement('a');
		vote.setAttribute('href', 'javascript:;');
		vote.setAttribute('class', 'vote link-light-blue');
		vote.setAttribute('onclick', 'client.vote_comment("' + commentid + '");');
		vote.innerHTML = 'like';
		
		var unvote = document.createElement('a');
		unvote.setAttribute('href', 'javascript:;');
		unvote.setAttribute('class', 'unvote link-light-blue');
		unvote.setAttribute('onclick', 'client.unvote_comment("' + commentid + '");');
		unvote.innerHTML = 'unlike';
		
		var td1 = document.createElement('div');
		td1.setAttribute('class', 'tinydot');
		td1.innerHTML = ".";
		
		var flag = document.createElement('a');
		flag.setAttribute('href', 'javascript:;');
		flag.setAttribute('class', 'flag link-light-blue');
		flag.setAttribute('onclick', 'client.flag_comment("' + commentid + '");');
		flag.innerHTML = 'flag';
		
		var unflag = document.createElement('a');
		unflag.setAttribute('href', 'javascript:;');
		unflag.setAttribute('class', 'unflag link-light-blue');
		unflag.setAttribute('onclick', 'client.unflag_comment("' + commentid + '");');
		unflag.innerHTML = 'unflag';
		
		if(canvote) {
			unvote.setAttribute('style', 'display:none;');
		} else {
			vote.setAttribute('style', 'display:none;');
		}
		
		if(canflag) {
			unflag.setAttribute('style', 'display:none;');
		} else {
			flag.setAttribute('style', 'display:none;');
		}
		
		comment_actions.appendChild(vote);
		comment_actions.appendChild(unvote);
		comment_actions.appendChild(td1);
		comment_actions.appendChild(flag);
		comment_actions.appendChild(unflag);
		return comment_actions;
	};

	var make_stats = function(flags, votes) {
		var stats = document.createElement('div');
		stats.setAttribute('class', 'stats');
		
		var plus = document.createElement('div');
		plus.setAttribute('class', 'plus-symbol');
		plus.innerHTML = '+';
		
		var votes_container = document.createElement('div');
		votes_container.setAttribute('class', 'votes_container');
		if (votes == 0) {
			votes_container.setAttribute('style', 'display:none;');
		}
		var votes_tag = document.createElement('div');
		votes_tag.setAttribute('class', 'votes');
		votes_tag.innerHTML = votes;
		
		var flags_tag = document.createElement('div');
		flags_tag.setAttribute('class', 'flags');
		if (flags == 0) {
			flags_tag.setAttribute('style', 'display:none;');
		}
		flags_tag.innerHTML = flags;
		
		stats.appendChild(votes_container)
		votes_container.appendChild(plus);
		votes_container.appendChild(votes_tag);
		stats.appendChild(flags_tag);
		return stats;
	};
	
	var hide_flagged = function(objectid) {
		var flag_message = document.createElement('div');
		flag_message.setAttribute('id', 'flag_message_for_' + objectid);
		flag_message.setAttribute('class', 'flag_message');
		flag_message.innerHTML = 'There was something here but it was flagged too many times. Click on this message to show it.';
		
		$('#' + objectid).css('display', 'none');
		$(flag_message).insertAfter('#' + objectid);
		
		$('#flag_message_for_' + objectid).bind('click', function() {
			$('#' + objectid).css('display', '');
			$(this).remove();
		});
	}
	
})();
