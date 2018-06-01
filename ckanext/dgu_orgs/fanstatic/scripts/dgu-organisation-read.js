'use strict';

(function ($) {
  var bind = $('.js-trigger-organisation-scroll');
  bind.on('shown.bs.dropdown', function () {
    var h = $('.organisation-dropdown');
    if (h.height() > 450) {
      h.scrollTop(0);
      var r = h.find('.organisation-row.active');
      var top = r.position().top - 300;
      h.scrollTop(top);
    }
  });
})(jQuery);