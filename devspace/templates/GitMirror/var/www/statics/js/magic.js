function setTheme() {
  var storage = window.localStorage;
  if (storage['theme'] == "light") {
    storage['theme'] = "dark"
  } else {
    storage['theme'] = "light"
  }
  window.location.reload()
}

function removeCSS() {
  links = document.getElementsByTagName("link")
  for (var i = 0; i < links.length; i++) {
    if (links[i] && links[i].getAttribute("href") != null && links[i]
      .getAttribute("href").indexOf("cgit") != -1) {
      links[i].parentNode.removeChild(links[i])
    }
  }
}

function loadCSS(file) {
  var link = document.createElement("link")
  link.setAttribute("rel", "stylesheet")
  link.setAttribute("type", "text/css")
  link.setAttribute("href", file)
  if (typeof link != "undefined") {
    document.getElementsByTagName("head")[0].appendChild(link)
  }
}

function magic() {
  if (!window.localStorage) {
    alert("Not support localstorage");
  } else {
    var repo = $(location).attr('pathname').split('/')[1]
    console.log(repo)
    var storage = window.localStorage;
    if (!storage['theme']) {
      storage['theme'] = "light"
    }
    if (storage['theme'] == "light") {
      button_text = 'dark theme'
      logo_img = '/statics/'+repo+'/logo-light.png'
      css_file = '/statics/css/cgit-light.css'
    } else {
      button_text = 'light theme'
      logo_img = '/statics/'+repo+'/logo-dark.png'
      css_file = '/statics/css/cgit-dark.css'
    }
    $(document).ready(function() {
      removeCSS()
      loadCSS(css_file)
      $('.logo').append(
        '<button onclick="setTheme()" style="background-color:transparent; color:blue; border:none; outline:none;">' +
        button_text + '</button>');
      $('.logo').find("img").attr("src", logo_img)
    });
  }
}