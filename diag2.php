<?php echo "User: " . get_current_user() . "
"; echo "File owner: " . fileowner("js/ui/interactions.js") . "
"; echo "Writable: " . is_writable("js/ui/interactions.js"); ?>
