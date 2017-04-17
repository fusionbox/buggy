jQuery(function($) {
  $('select[name="projects"]').select2();

  $('body').on('submit', 'form.add-preset', function(e) {
    e.preventDefault();
    $.post($(this).attr('action'), $(this).serialize()).done(
      function(data, textState, jqXRH) {
        $('form.add-preset').find('input[type=text]').val('');
        var element = $(data['html']);
        var id = element.attr('id');
        var added = false
        $('.preset-item').each(function() {
          if ($(this).attr('id') > id) {
            element.insertBefore($(this));
            added = true;
            return false;
          }
        });
        if (!added) $(element).appendTo($('.preset-container'));
      }
    );
  });

  $('body').on('submit', 'form.remove-preset', function(e) {
    e.preventDefault();
    $.post($(this).attr('action'), $(this).serialize()).done(
      function(data, textStatus, jqXHR) {
        $("#preset-" + data['slug']).remove();
      }
    );
  });
});
