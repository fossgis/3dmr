function addComment() {
	var comment = document.getElementById("comment");

	// refuse if comment is empty
	if(comment.value == "") {
		alert("Empty comments aren't allowed.");
		return false;
	}

	var request = new XMLHttpRequest();
	var comment_url = "/action/addcomment";
	request.open("POST", comment_url, true);
	request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
	request.onreadystatechange = function() {
		if(request.readyState == 4 && request.status == 200)
			commentAdded(request.responseText);
	};
	
	var form = document.getElementById("comment_form");
	var csrf = form.children[0];

	var params = "comment=" + encodeURIComponent(comment.value);
	params += "&" + csrf.name + "=" + csrf.value;
	params += "&model_id=" + model_id + "&revision=" + revision;
	request.send(params);

	comment.value = "";

	return false;
}

function commentAdded(json) {
	var fields = JSON.parse(json)

	if(fields["success"] == "no") {
		alert(fields["error"]);
		return;
	}

	var html = '<div class="panel panel-default">';

	html += '<div class="panel-body panel-new"';
	html += fields["comment"];
	html += '</div>'; // end of .panel-body

	html += '<div class="panel-footer">';
	html += '<a href="/user/' + fields["author"] + '">';
	html += '<span class="label label-default">'
	html += fields["author"];
	html += '</span>';
	html += '</a>'

	// possibly find a library for this?
	var datetime = new Date(fields.datetime);
	var datestr = datetime.getFullYear() + "-"
	datestr += ("0" + (datetime.getMonth() + 1)).slice(-2) + "-";
	datestr += ("0" + (datetime.getDate())).slice(-2) + " ";
	datestr += ("0" + (datetime.getHours())).slice(-2) + ":";
	datestr += ("0" + (datetime.getMinutes())).slice(-2);

	html += ' on ' + datestr;
	html += '</div>'; // end of .panel-footer

	html += '</div>'; // end of .panel.panel-default
	
	// we'll place the returned comment after this element
	var previousElement = document
		.getElementById("comment_form")
		.parentElement
		.children[1]
	previousElement.insertAdjacentHTML("afterEnd", html);
	previousElement.scrollIntoView();
}
