// Create a "packed" structure data type which is similar to creating
// bit [7:0]  ctrl_reg;
// ctrl_reg [0]   represents en
// ctrl_reg [3:1] represents cfg
// ctrl_reg [7:4] represents mode
typedef struct packed {
  bit [3:0] mode;
  bit [2:0] cfg;
  bit       en;
} st_ctrl;

module tb;
  st_ctrl    ctrl_reg;

  initial begin
    // Initialize packed structure variable
    ctrl_reg = '{4'ha, 3'h5, 1};
    $display ("ctrl_reg = %p", ctrl_reg);

    // Change packed structure member to something else
    ctrl_reg.mode = 4'h3;
    $display ("ctrl_reg = %p", ctrl_reg);

    // Assign a packed value to the structure variable
    ctrl_reg = 8'hfa;
    $display ("ctrl_reg = %p", ctrl_reg);
  end
endmodule
