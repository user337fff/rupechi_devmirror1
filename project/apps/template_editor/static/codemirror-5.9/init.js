document.addEventListener('DOMContentLoaded', function(){ 
    document.querySelectorAll('textarea.html-editor').forEach(function(el, idx){
        myCodeMirror = CodeMirror.fromTextArea(el, {
            lineNumbers: true,
            // mode: 'htmlmixed',
            mode: 'text/x-django',
            theme: 'lucario'
        });
        myCodeMirror.setSize(null, 700);
    });
});