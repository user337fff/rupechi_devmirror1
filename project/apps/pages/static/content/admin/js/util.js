function requests(data, action, method, success = function(response) {}, error = function(error) {}) {
    var url = new URL(action)

    method = method.toLowerCase()
    if (method == 'get') url.search = data

    return new Promise(function(resolve, reject) {
        var xhr = new XMLHttpRequest()

        xhr.open(method, url.href, true)
        if (method === 'post') {
            if (typeof(data) === 'string') {
                xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded')
            }
        }
        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest")
        xhr.onload = function() {
            if (this.status == 200) {
                resolve(JSON.parse(this.response))
            } else {
                var err = new Error(this.statusText)
                err.code = this.status
                reject(err)
            }
        }
        xhr.send(data)
    }).then(success, error)
}

function serializeForm(form) {
    var formData = new FormData(form)
    var arrayData = new Array()
    var data = new String()
    
    for (var item of formData.entries()) {
        arrayData.push(item)
    }
    arrayData.forEach(function(item, index) {
        if (index) data += '&'
        data += item[0] + '=' + encodeURIComponent(item[1])
    })

    return data
}

function parseHTML(markup) {
    var parser = new DOMParser()
    var body = parser.parseFromString(markup, "text/html").body
    if (body.children.length > 1) {
        var elements = new Array()
        Array.prototype.slice.call(body.children).forEach(function(item) {
            elements.push(item)
        })
        return elements
    } else {
        return body.firstChild
    }
}

function parseHTMLArray(markups) {
    var _this = this
    var elements = Array()
    markups.forEach(function(markup) {
        elements.push(_this.parseHTML(markup))
    })
    return elements
}

function parseArray(nodes) {
    return Array.prototype.slice.call(nodes)
}

function offset(element) {
    var rect = element.getBoundingClientRect(),
    scrollLeft = window.pageXOffset || document.documentElement.scrollLeft
    scrollTop = window.pageYOffset || document.documentElement.scrollTop
    return { top: rect.top + scrollTop, left: rect.left + scrollLeft }
}

function svgRepairUse() {
    var allSVG = Array.prototype.slice.call(document.querySelectorAll('svg'))
    allSVG.forEach(function(svg) {
        if (svg.firstElementChild.href !== undefined) {
            var href = svg.firstElementChild.href.baseVal
            var use = document.createElementNS('http://www.w3.org/2000/svg', 'use')
            use.setAttributeNS('http://www.w3.org/1999/xlink', 'href', href)
            svg.firstElementChild.remove()
            svg.appendChild(use)
        }
    })
}

function createSVG(href, className = '') {
    var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg")
    var use = document.createElementNS('http://www.w3.org/2000/svg', 'use')
    use.setAttributeNS('http://www.w3.org/1999/xlink', 'href', href)
    svg.classList.add(className)
    svg.appendChild(use)
    return svg
}
