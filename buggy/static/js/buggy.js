jQuery(function($) {
  $('select[name="projects"]').select2();
  $('select[name="project"]').select2();

  $('.actions .subActions').hide();
  $('.nestedAction .open').click(function() {
    $('.actions > button, .actions .open').hide();
    $(this).closest('.nestedAction').find('.subActions').show();
    return false;
  });

  $('.subActions .cancel').click(function() {
    $(this).closest('.nestedAction').find('.subActions').hide();
    $('.actions > button, .actions .open').show();
    return false;
  });
});
