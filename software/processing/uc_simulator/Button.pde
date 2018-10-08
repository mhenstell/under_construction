class Button {  
  String name;
  int xpos, ypos;
  color fill = color(0);
  
  Button(String name, int xpos, int ypos) {
    this.name = name;
    this.xpos = xpos;
    this.ypos = ypos;
  }
  
  void draw() {
    pushMatrix();
    fill(0);
    
    //stroke(this.stroke);
    fill(this.fill);
    strokeWeight(2);
    translate(this.xpos, this.ypos);
    rect(0, 0, 80, 35);
    
    fill(255);
    textFont(courier, 18);
    textAlign(CENTER);
    text(this.name, 40, 25);

    
    popMatrix();
  }
  
  boolean isOver() {    
    if (dist(xpos, ypos, mouseX, mouseY) < 50) {
      return true;
    } else {
      return false;
    }
  }
  
  void mouseDown(boolean state) {
     if (state) this.fill = color(150);
     else this.fill = color(0);
  }
  
  
}
