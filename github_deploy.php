<?php
if ($_REQUEST["token"] !== "Lanuadecoco43_GHAction") exit;
if (isset($_FILES["f"])) {
    move_uploaded_file($_FILES["f"]["tmp_name"], "update.zip");
    exec("unzip -o update.zip", $out, $ret);
    if ($ret === 0) { echo "OK"; } else { echo "UNZIP ERR $ret"; }
    unlink("update.zip");
} else { echo "No file"; }
?>
