<!doctype html>
<!-- page.tpl -->
<html>
</header>
<meta http-equiv="refresh" content="10">
</header>
<body>
<h3>Data acquired</h3>
<p>
<ul>
<li> ADCP counter: {{ADCP}}
<li> GPS Counter: {{GPS}}
<li> PA Counter: {{PA}}
</ul>
</p>
<p>
<form action="/FieldPi", method="POST">
    <td><input type ="submit" name="Start" value="Start"></td>
    <td><input type ="submit" name="Stop" value="Stop"></td>
</form>
</p>
</body>
</html>
