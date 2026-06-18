package com.example.demoRegistry;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.beans.factory.annotation.Value;

@SpringBootApplication
@RestController
public class DemoRegistryApplication {

	@Value("${db.pass}")
    private String secret;

	public static void main(String[] args) {
		SpringApplication.run(DemoRegistryApplication.class, args);
	}

	@GetMapping("/")
    public String index() {
        return "<h1>Teste do registry</h1>" +
               "<hr>" +
               "<h3>" + secret + "</h3>";
    }

}
