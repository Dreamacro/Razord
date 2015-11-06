//http://stackoverflow.com/a/2648463 - wizardry!
String.prototype.format = String.prototype.f = function() {
    var s = this,
        i = arguments.length;

    while (i--) {
        s = s.replace(new RegExp('\\{' + i + '\\}', 'gm'), arguments[i]);
    }
    return s;
};

function htmlentities(string) {
    return $('<div/>').text(string).html();
}

//http://stackoverflow.com/a/7616484
String.prototype.hashCode = function() {
    var hash = 0, i, chr, len;
    if (this.length == 0) return hash;
    for (i = 0, len = this.length; i < len; i++) {
        chr   = this.charCodeAt(i);
        hash  = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
};

var challenges;

function loadchal(id) {
    var obj = $.grep(challenges['game'], function (e) {
        return e.id == id;
    })[0]
    window.location.hash = obj.name
    $('#chal-window .chal-name').text(obj.name)
    $('#chal-window .chal-desc').html(marked(obj.description, {'gfm':true, 'breaks':true}))

    for (var i = 0; i < obj.files.length; i++) {
        var filename = obj.files[i].split('/')
        filename = filename[filename.length - 1]
        $('#chal-window .chal-desc').append("<a href='"+obj.files[i]+"'>"+filename+"</a><br/>")
    };

    $('#chal-window .chal-value').text(obj.value)
    $('#chal-window .chal-category').text(obj.category)
    $('#chal-window #chal-id').val(obj.id)
    $('#chal-window .chal-solves').text(obj.solves + " solves")
    $('#answer').val("")

    $('pre code').each(function(i, block) {
        hljs.highlightBlock(block);
    });
    $('#chal-window').foundation('reveal', 'open');
}

function loadchalbyname(chalname) {
  var obj = $.grep(challenges['game'], function (e) {
      return e.name == chalname;
  })[0];
  window.location.hash = obj.name
  $('#chal-window .chal-name').text(obj.name)
  $('#chal-window .chal-desc').html(marked(obj.description, {'gfm':true, 'breaks':true}))

  for (var i = 0; i < obj.files.length; i++) {
      var filename = obj.files[i].split('/')
      filename = filename[filename.length - 1]
      $('#chal-window .chal-desc').append("<a href='"+obj.files[i]+"'>"+filename+"</a><br/>")
  };

  $('#chal-window .chal-value').text(obj.value);
  $('#chal-window .chal-category').text(obj.category);
  $('#chal-window #chal-id').val(obj.id);
  $('#chal-window .chal-solves').text(obj.solves + " solves");
  $('#answer').val("");

  $('pre code').each(function(i, block) {
      hljs.highlightBlock(block);
  });
  
  $('#chal-window').foundation('reveal', 'open');
}


$("#answer").keyup(function(event){
    if(event.keyCode == 13){
        $("#submit-key").click();
    }
});


function submitkey(key, nonce) {
    $.post("/submit_flag", {
        key: key, 
        nonce: nonce
    }, function (data) {
        var submitKey = $('#submit-key');
        if (data['status'] == -1){
          window.location = "/login";
          return;
        }
        submitKey
            .text(data['msg'])
            .prop('disabled', true);
        if (data['status'] == 0){ // Incorrect key
            submitKey.css('background-color', 'red');
        }
        else if (data['status'] == 1){ // Challenge Solved
            submitKey.css('background-color', 'green');
            //var chalSolves = $('#chal-window .chal-solves');
            //chalSolves.text( (parseInt(chalSolves.text().split(" ")[0]) + 1 +  " solves") );
        }/*
        else if (data['status'] == 2){ // Challenge already solved
            submitKey
                
        }/*
        else if (data['status'] == 3){ // Keys per minute too high
            submitKey
                .text("You're submitting keys too fast. Slow down.")
                .css('background-color', '#e18728')
                .prop('disabled', true);
        }
        else if (data['status'] == 4){ // too many incorrect solves
            submitKey
                .text('Too many attempts.')
                .css('background-color', 'red')
                .prop('disabled', true);
        }*/
        marktoomanyattempts()
        marksolves()
        updatesolves()
        setTimeout(function() {
            submitKey
                .text('Submit')
                .prop('disabled', false)
                .css('background-color', '#007095');
        }, 3000);
    })
}

function marksolves() {
    $.get('/solves', function (data) {
        var solves = data;//$.parseJSON(JSON.stringify(data));
        for (var i = solves['solves'].length - 1; i >= 0; i--) {
            var id = solves['solves'][i].chalid;
            $('#challenges button[value="' + id + '"]')
                .addClass('secondary')
                .css('opacity', '0.3');
            //$('#challenges button[value="' + id + '"]').css('opacity', '0.3')
        };
        if (window.location.hash.length > 0){
          loadchalbyname(window.location.hash.substring(1))
        }
    });
}

function marktoomanyattempts() {
    $.get('/maxattempts', function (data) {
        var maxattempts = data;//$.parseJSON(JSON.stringify(data));
        for (var i = maxattempts['maxattempts'].length - 1; i >= 0; i--) {
            var id = maxattempts['maxattempts'][i].chalid;
            $('#challenges button[value="' + id + '"]')
                .addClass('secondary')
                .css('background-color', '#FF9999');
            //$('#challenges button[value="' + id + '"]').css('background-color', '#FF9999');
        };
        if (window.location.hash.length > 0){
          loadchalbyname(window.location.hash.substring(1))
        }
    });
}

function updatesolves(){
    $.get('/chals/solves', function (data) {
      var solves = data;//$.parseJSON(JSON.stringify(data));
      var chals = Object.keys(solves);
      var obj;

      for (var i = 0; i < chals.length; i++) {  
        obj = $.grep(challenges['game'], function (e) {
            return e.name == chals[i];
        })[0];
        obj.solves = solves[chals[i]]
      };

    });
}

function getsolves(id){
  $.get('/chal/'+id+'/solves', function (data) {
    var teams = data['teams'];
    var box = $('#chal-solves-names');
    box.empty();
    for (var i = 0; i < teams.length; i++) {
      var id = teams[i].id;
      var name = teams[i].name;
      var date = moment(teams[i].date).local().format('LLL');
      box.append('<tr><td><a href="/team/{0}">{1}</td><td>{2}</td></tr>'.format(id, htmlentities(name), date));
    };
  });
}

$('#submit-key').click(function (e) {
    submitkey($('#answer').val(), $('#nonce').val())
});

$('.chal-solves').click(function (e) {
    getsolves($('#chal-id').val())
});

// $.distint(array)
// Unique elements in array
$.extend({
    distinct : function(anArray) {
       var result = [];
       $.each(anArray, function(i,v){
           if ($.inArray(v, result) == -1) result.push(v);
       });
       return result;
    }
});

$(document).on('close', '[data-reveal]', function () {
  window.location.hash = ""
});

$(function() {
    $.get("/chals", function (data) {
        var categories = [];
        challenges = data;//$.parseJSON(JSON.stringify(data));

        for (var i = challenges['game'].length - 1; i >= 0; i--) {
            challenges['game'][i].solves = 0
            if ($.inArray(challenges['game'][i].category, categories) == -1) {
                categories.push(challenges['game'][i].category)
                $('#challenges').append($('<tr id="' + challenges['game'][i].category.replace(/ /g,"-").hashCode() + '"><td class="large-2"><h4>' + challenges['game'][i].category + '</h4></td></tr>'))
            }
        };

        for (var i = 0; i <= challenges['game'].length - 1; i++) {
            var chal = challenges['game'][i]
            var chal_button = $('<button class="chal-button" value="{0}"><p>{1}</p><span>{2}</span></button>'.format(chal.id, chal.name, chal.value))
            $('#' + challenges['game'][i].category.replace(/ /g,"-").hashCode()).append(chal_button);
        };
        updatesolves(challenges);
        marktoomanyattempts()
        marksolves()

        $('#challenges button').click(function (e) {
            loadchal(this.value);
        });

    });
});
