require("@nomicfoundation/hardhat-toolbox");

module.exports = {
  solidity: "0.8.18",
  networks: {
    ganache: {
      url: "http://127.0.0.1:7545",
      accounts: ["0x2962883fe387707b6a47c537c27d03c2918fc7bdb0f60939c25cdff07643b362"], 
    }
  }
};

