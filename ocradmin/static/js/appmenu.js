//
// Menus
//

$(function() {
    function deactivateMenu(menu) {
        $(menu).removeClass("ui-selected")
            .unbind("click.menuclose")
            .find("ul").hide();
        $(".dropdownmenu > ul.top").unbind("mouseenter.menuover");
        $(window).unbind("click.menuclose");
        $(window).unbind("keydown.menuclose");
        $(menu).bind("click.menuopen", function(event) {
            activateMenu(this);
        });
    }

    function activateMenu(menu) {
        $(".dropdownmenu > ul.top").not($(menu)).each(function(i, elem) {
            deactivateMenu(elem);
        }).bind("mouseenter.menuover", function(event) {
            activateMenu(this);
        });
        $(menu)
            .addClass("ui-selected")
            .unbind("click.menuopen")
            .bind("click.menuclose", function(event) {
                deactivateMenu(menu);
            }).find("ul").show()
            .find("li").not(".separator").bind("mouseenter", function(event) {
                $(this).addClass("ui-selected");
            }).bind("mouseleave", function(event) {
                $(this).removeClass("ui-selected");
            });
        $(window)
            .bind("keydown.menuclose", function(event) {
                if (event.keyCode == KC_ESCAPE) {
                    deactivateMenu(menu);
                    $(".dropdownmenu > ul.top").unbind("click.menuclose");
                    $(window).unbind("keydown.menuclose");
                } else if (event.keyCode == KC_LEFT) {
                    if (menu.previousElementSibling) {
                        activateMenu(menu.previousElementSibling);
                    }
                } else if (event.keyCode == KC_RIGHT) {
                    if (menu.nextElementSibling) {
                        activateMenu(menu.nextElementSibling);
                    }
                }
            }).bind("click.menuclose", function(event) {
                if (event.pageX > $(menu).offset().left &&
                    event.pageX < $(menu).offset().left +
                        $(menu).width() &&
                    event.pageY > $(menu).offset().top &&
                    event.pageY < $(menu).offset().top +
                        $(menu).height()) {
                    return true;
                }
                deactivateMenu(menu);
            });
    }

    // active main menu click dropdown
    $(".dropdownmenu > ul.top").bind("click.menuopen", function(e1) {
        activateMenu(this);
    });
    
    // active main menu click dropdown
    $(".dropdownmenu > ul.top ul li").bind("click.launch", function(e1) {
        deactivateMenu(this);
    });
});
