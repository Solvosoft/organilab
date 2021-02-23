$(document).ready(function(){
  CKEDITOR.on('dialogDefinition', function(ev) {
    // Take the dialog name and its definition from the event data.
    var dialogName = ev.data.name;
    var dialogDefinition = ev.data.definition;

    // Check if the definition is from the dialog we're
    // interested in (the 'link' dialog).
    if (dialogName == 'link') {
      // Remove the 'Upload' and 'Advanced' tabs from the 'Link' dialog.
      // dialogDefinition.removeContents('upload');
      // dialogDefinition.removeContents('advanced');

      // Get a reference to the 'Link Info' tab.
      var infoTab = dialogDefinition.getContents('info');

      // Get a reference to the "Target" tab and set default to '_blank'
      var targetTab = dialogDefinition.getContents('target');
      var targetField = targetTab.get('linkTargetType');
      targetField['default'] = '_blank';
    }
  });
});
