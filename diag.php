<?php error_reporting(E_ALL); echo "Disk free: " . round(disk_free_space(".") / 1024 / 1024, 2) . " MB
"; ?>
