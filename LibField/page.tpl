<!doctype html>
<!-- page.tpl -->
<html>
<header>
<style>
% for line in css:
  {{line}}
% end
</style>
<meta http-equiv="refresh" content="10">
</header>
<body>
<div id="container">
<div id="content">
<h1>Data</h1>

<h2> ADCP data dictionnary</h2>
<table>
<tr><th> Field </th><th> value</th></tr>
% for key,val in ADCP.items():
<tr>
  <td> {{key}} </td><td>{{val}}</td>
</tr>
% end
</table>

<h2>GPS</h2>
<table>
<tr><th> Field </th><th> Value</th></tr>
% for key,val in GPS.items():
<tr>
  <td> {{key}} </td><td>{{val}}</td>
</tr>
% end
</table>


<h2> PA 500</h2>
% t = PA[0]
% z = PA[1]
<table>
  <tr><th> Time </th><th> Depth (m)</th></tr>
  <tr>
    <td> {{t}} </td><td>{{z}}</td>
  </tr>
</table>
</p>
<p style="text-align:center;">
<form action="/FieldPi", method="POST">
    <td><input type ="submit" name="Start" value="Start" style="width:45%;height:50px;margin-right:9%;background-color:#004D9B;color:white;"></td>
    <td><input type ="submit" name="Stop" value="Stop" style="width:45%;height:50px;background-color:#F13C4F;color:white;"></td>
</form>
</p>
</div>
</div>
</body>
</html>
