<?php echo "Server time: ".date("c")."
"; foreach (glob("js/ui/*") as $f) { echo "$f - " . filesize($f) . " bytes - " . date("c", filemtime($f)) . "
"; } ?>
